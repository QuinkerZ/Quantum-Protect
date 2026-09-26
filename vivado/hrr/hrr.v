`timescale 1ns / 1ps

// ============================================================
// HRR modular multiplication for ML-KEM / Kyber q = 3329.
//
// Computes:
//     r = (a * b) mod Q
//
// Fixed/default parameters:
//     Q       = 3329
//     R       = 4096 = 2^12
//     MU      = floor(2^24 / Q) = 5039
//     Q_PRIME = -Q^(-1) mod R = 3327
//
// Pipeline:
//     latch inputs
//       -> Barrett conversion to Montgomery domain
//       -> Montgomery multiplication
//       -> REDC
//       -> REDC back to normal domain
//       -> done pulse
//
// Interface:
//     clk  : clock
//     rst  : synchronous active-high reset
//     start: begin one operation when asserted in S_IDLE
//     a,b  : 12-bit operands, each in [0,Q-1]
//     r    : 12-bit reduced result
//     done : one-cycle pulse when r is valid
//
// IMPORTANT:
// All intermediate multiplication operands are explicitly widened.
// This avoids Verilog expression-sizing/truncation problems when the
// integer parameters MU and Q_PRIME are used in multiplications.
// ============================================================

module hrr #(
    parameter integer Q = 3329,
    parameter integer R = 4096,
    parameter integer MU = 5039,
    parameter integer Q_PRIME = 3327
)(
    input  wire        clk,
    input  wire        rst,
    input  wire        start,
    input  wire [11:0] a,
    input  wire [11:0] b,
    output reg  [11:0] r,
    output reg         done
);

    // The current ML-KEM parameter set fits in these widths.
    localparam [11:0] Q_CONST  = Q;
    localparam [12:0] MU_CONST = MU;
    localparam [11:0] QP_CONST = Q_PRIME;

    localparam [3:0] S_IDLE      = 4'd0;
    localparam [3:0] S_BARRETT_A = 4'd1;
    localparam [3:0] S_BARRETT_B = 4'd2;
    localparam [3:0] S_MULTIPLY  = 4'd3;
    localparam [3:0] S_REDC_1    = 4'd4;
    localparam [3:0] S_REDC_2    = 4'd5;
    localparam [3:0] S_DONE      = 4'd6;

    reg [3:0] state;

    reg [11:0] a_reg;
    reg [11:0] b_reg;
    reg [11:0] a_bar;
    reg [11:0] b_bar;
    reg [23:0] T;

    // --------------------------------------------------------
    // Barrett conversion combinational intermediates.
    // --------------------------------------------------------
    wire [23:0] barrett_x_a = {a_reg, 12'b0};
    wire [23:0] barrett_x_b = {b_reg, 12'b0};

    // Both operands are widened to 37 bits before multiplication.
    // The true product needs at most 24 + 13 = 37 bits.
    wire [36:0] barrett_product_a =
        {13'b0, barrett_x_a} * {24'b0, MU_CONST};
    wire [36:0] barrett_product_b =
        {13'b0, barrett_x_b} * {24'b0, MU_CONST};

    wire [12:0] q_hat_a = barrett_product_a[36:24];
    wire [12:0] q_hat_b = barrett_product_b[36:24];

    // q_hat * Q needs at most 13 + 12 = 25 bits.
    wire [24:0] barrett_q_product_a =
        {12'b0, q_hat_a} * {13'b0, Q_CONST};
    wire [24:0] barrett_q_product_b =
        {12'b0, q_hat_b} * {13'b0, Q_CONST};

    wire [24:0] barrett_t_a =
        {1'b0, barrett_x_a} - barrett_q_product_a;
    wire [24:0] barrett_t_b =
        {1'b0, barrett_x_b} - barrett_q_product_b;

    wire [24:0] barrett_red_a =
        (barrett_t_a >= {13'b0, Q_CONST}) ?
        (barrett_t_a - {13'b0, Q_CONST}) : barrett_t_a;
    wire [24:0] barrett_red_b =
        (barrett_t_b >= {13'b0, Q_CONST}) ?
        (barrett_t_b - {13'b0, Q_CONST}) : barrett_t_b;

    // --------------------------------------------------------
    // Montgomery REDC combinational intermediates.
    // --------------------------------------------------------
    // T needs 24 bits and Q_PRIME needs 12 bits; use 36-bit
    // operands so the full product is preserved.
    wire [35:0] mont_product =
        {12'b0, T} * {24'b0, QP_CONST};

    wire [11:0] mont_m = mont_product[11:0];

    // m * Q needs at most 12 + 12 = 24 bits; sum with T needs 25.
    wire [23:0] mont_mq =
        {12'b0, mont_m} * {12'b0, Q_CONST};

    wire [24:0] mont_sum = {1'b0, T} + {1'b0, mont_mq};
    wire [12:0] mont_u = mont_sum[24:12];

    wire [12:0] mont_red =
        (mont_u >= {1'b0, Q_CONST}) ?
        (mont_u - {1'b0, Q_CONST}) : mont_u;

    // --------------------------------------------------------
    // Sequential controller.
    // --------------------------------------------------------
    always @(posedge clk) begin
        if (rst) begin
            state <= S_IDLE;
            a_reg <= 12'd0;
            b_reg <= 12'd0;
            a_bar <= 12'd0;
            b_bar <= 12'd0;
            T <= 24'd0;
            r <= 12'd0;
            done <= 1'b0;
        end else begin
            // done is a one-cycle pulse.
            done <= 1'b0;

            case (state)
                S_IDLE: begin
                    if (start) begin
                        a_reg <= a;
                        b_reg <= b;
                        state <= S_BARRETT_A;
                    end
                end

                // a_bar = (a * R) mod Q
                S_BARRETT_A: begin
                    a_bar <= barrett_red_a[11:0];
                    state <= S_BARRETT_B;
                end

                // b_bar = (b * R) mod Q
                S_BARRETT_B: begin
                    b_bar <= barrett_red_b[11:0];
                    state <= S_MULTIPLY;
                end

                // T = a_bar * b_bar
                S_MULTIPLY: begin
                    T <= a_bar * b_bar;
                    state <= S_REDC_1;
                end

                // First REDC keeps the product in Montgomery domain.
                S_REDC_1: begin
                    T <= {12'b0, mont_red};
                    state <= S_REDC_2;
                end

                // Second REDC converts the result to normal domain.
                S_REDC_2: begin
                    r <= mont_red[11:0];
                    state <= S_DONE;
                end

                S_DONE: begin
                    done <= 1'b1;
                    state <= S_IDLE;
                end

                default: begin
                    state <= S_IDLE;
                end
            endcase
        end
    end

endmodule
