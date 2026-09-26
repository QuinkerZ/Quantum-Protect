import base64

svg = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 170 170" fill="none">'
    '<ellipse cx="80" cy="80" rx="72" ry="26" stroke="#54655B" stroke-width="5.5" transform="rotate(-26 80 80)" />'
    '<circle cx="128" cy="42" r="8" fill="#54655B" />'
    '<circle cx="80" cy="80" r="46" stroke="#192024" stroke-width="16" fill="none" />'
    '<line x1="64" y1="64" x2="114" y2="114" stroke="#192024" stroke-width="16" stroke-linecap="square" />'
    '</svg>'
)

encoded = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
print('data:image/svg+xml;base64,' + encoded)
