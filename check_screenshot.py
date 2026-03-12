import struct, zlib

with open('/Volumes/CodeSSD/thorvg-development/ThorKivy/thorkivy_demo.png', 'rb') as f:
    sig = f.read(8)
    idat_chunks = []
    width = height = 0
    while True:
        hdr = f.read(8)
        if len(hdr) < 8:
            break
        length, ctype = struct.unpack('>I4s', hdr)
        data = f.read(length)
        crc = f.read(4)
        ctype = ctype.decode('ascii')
        if ctype == 'IHDR':
            width, height = struct.unpack('>II', data[:8])
            bit_depth = data[8]
            color_type = data[9]
            print(f'IHDR: {width}x{height}, depth={bit_depth}, ctype={color_type}')
        elif ctype == 'IDAT':
            idat_chunks.append(data)

    raw = zlib.decompress(b''.join(idat_chunks))
    print(f'Decompressed size: {len(raw)} bytes')

    stride = 1 + width * 3
    colors = {}
    for y in range(height):
        row_start = y * stride + 1
        for x in range(0, width, 50):
            idx = row_start + x * 3
            r = raw[idx]
            g = raw[idx + 1]
            b = raw[idx + 2]
            c = (r, g, b)
            colors[c] = colors.get(c, 0) + 1

    sorted_colors = sorted(colors.items(), key=lambda x: -x[1])
    print(f'Sampled {sum(colors.values())} pixels, {len(colors)} unique colors')
    for c, n in sorted_colors[:15]:
        print(f'  {n:5d} px: rgb{c}')

    # Also sample specific known locations from __main__.py
    # Red rect at (50,50) size (200,100)
    # Green rounded rect at (300,30) size (180,120)
    # Blue circle center (400,350) radius 80
    # Yellow triangle at (600,200)
    # Magenta quad at (50,350)
    # Kivy yellow rect at (10,10) size (780,580)
    print("\nSpecific pixel samples:")
    spots = [(100, 80, "red rect area"), (350, 60, "rounded rect area"),
             (400, 350, "circle area"), (600, 250, "triangle area"),
             (100, 400, "quad area"), (400, 300, "center")]
    for x, y, label in spots:
        if 0 <= x < width and 0 <= y < height:
            idx = y * stride + 1 + x * 3
            print(f'  ({x:3d},{y:3d}) [{label:20s}]: rgb({raw[idx]},{raw[idx+1]},{raw[idx+2]})')
