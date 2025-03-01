function processPlyBuffer(inputBuffer) {
    console.log("skipping converting");
    //const ubuf = new Uint8Array(inputBuffer);
    ubuf = inputBuffer;
    console.log("conver complete");
    // 10KB ought to be enough for a header
    const header = new TextDecoder().decode(ubuf.slice(0, 1024 * 10));
    const header_end = "end_header\n";
    const header_end_index = header.indexOf(header_end);
    if (header_end_index < 0)
        throw new Error("Unable to read .ply file header");
    const vertexCount = parseInt(/element vertex (\d+)\n/.exec(header)[1]);
    console.log("vertex count = " + vertexCount);
    console.log("Vertex Count", vertexCount);
    let row_offset = 0,
        offsets = {},
        types = {};
    const TYPE_MAP = {
        double: "getFloat64",
        int: "getInt32",
        uint: "getUint32",
        float: "getFloat32",
        short: "getInt16",
        ushort: "getUint16",
        uchar: "getUint8",
    };
    function filter_function(k){
        return k.startsWith("property ")
    }
    const headerSlice = header.slice(0, header_end_index).split("\n").filter(filter_function);
    for (let i = 0; i < headerSlice.length; i++) {
        let prop = headerSlice[i];
        let splitProp = prop.split(" ");
        let p = splitProp[0];
        let type = splitProp[1];
        let name = splitProp[2];
        let arrayType = TYPE_MAP[type] || "getInt8";
        types[name] = arrayType;
        offsets[name] = row_offset;
        row_offset += parseInt(arrayType.replace(/[^\d]/g, "")) / 8;
    }
    console.log("Bytes per row", row_offset, types, offsets);

    let dataView = new DataView(inputBuffer,header_end_index + header_end.length);
    let row = 0;

    function createAttrs(dataView, types, row, row_offset, offsets) {
        return {
            get(prop) {
                if (!types[prop]) throw new Error(prop + " not found");
                return dataView[types[prop]](
                    row * row_offset + offsets[prop],
                    true
                );
            }
        };
    }
    
    const attrs = createAttrs(dataView, types, row, row_offset, offsets);

    console.time("calculate importance");
    let sizeList = new Float32Array(vertexCount);
    let sizeIndex = new Uint32Array(vertexCount);
    for (row = 0; row < vertexCount; row++) {
        sizeIndex[row] = row;
        if (!types["scale_0"]) continue;
        const size =
            Math.exp(attrs.scale_0) *
            Math.exp(attrs.scale_1) *
            Math.exp(attrs.scale_2);
        const opacity = 1 / (1 + Math.exp(-attrs.opacity));
        sizeList[row] = size * opacity;
    }
    console.timeEnd("calculate importance");

    console.time("sort");
    function sort_function(b, a){
        return sizeList[a] - sizeList[b]
    }
    sizeIndex.sort(sort_function);
    console.timeEnd("sort");

    // 6*4 + 4 + 4 = 8*4
    // XYZ - Position (Float32)
    // XYZ - Scale (Float32)
    // RGBA - colors (uint8)
    // IJKL - quaternion/rot (uint8)
    const rowLength = 3 * 4 + 3 * 4 + 4 + 4;
    const buffer = new ArrayBuffer(rowLength * vertexCount);

    console.time("build buffer");
    for (let j = 0; j < vertexCount; j++) {
        row = sizeIndex[j];

        const position = new Float32Array(buffer, j * rowLength, 3);
        const scales = new Float32Array(buffer, j * rowLength + 4 * 3, 3);
        const rgba = new Uint8ClampedArray(
            buffer,
            j * rowLength + 4 * 3 + 4 * 3,
            4
        );
        const rot = new Uint8ClampedArray(
            buffer,
            j * rowLength + 4 * 3 + 4 * 3 + 4,
            4
        );

        if (types["scale_0"]) {
            const qlen = Math.sqrt(
                Math.pow(attrs.rot_0, 2) +
                Math.pow(attrs.rot_1, 2) +
                Math.pow(attrs.rot_2, 2) +
                Math.pow(attrs.rot_3, 2)
            );

            rot[0] = (attrs.rot_0 / qlen) * 128 + 128;
            rot[1] = (attrs.rot_1 / qlen) * 128 + 128;
            rot[2] = (attrs.rot_2 / qlen) * 128 + 128;
            rot[3] = (attrs.rot_3 / qlen) * 128 + 128;

            scales[0] = Math.exp(attrs.scale_0);
            scales[1] = Math.exp(attrs.scale_1);
            scales[2] = Math.exp(attrs.scale_2);
        } else {
            scales[0] = 0.01;
            scales[1] = 0.01;
            scales[2] = 0.01;

            rot[0] = 255;
            rot[1] = 0;
            rot[2] = 0;
            rot[3] = 0;
        }

        position[0] = attrs.x;
        position[1] = attrs.y;
        position[2] = attrs.z;

        if (types["f_dc_0"]) {
            const SH_C0 = 0.28209479177387814;
            rgba[0] = (0.5 + SH_C0 * attrs.f_dc_0) * 255;
            rgba[1] = (0.5 + SH_C0 * attrs.f_dc_1) * 255;
            rgba[2] = (0.5 + SH_C0 * attrs.f_dc_2) * 255;
        } else {
            rgba[0] = attrs.red;
            rgba[1] = attrs.green;
            rgba[2] = attrs.blue;
        }
        if (types["opacity"]) {
            rgba[3] = (1 / (1 + Math.exp(-attrs.opacity))) * 255;
        } else {
            rgba[3] = 255;
        }
    }
    console.timeEnd("build buffer");
    return buffer;
}





function customFunction(param) {
    console.log('Calling customFunction with param:', param);

}

function extractFileName(filePath) {
    const fileNameWithExtension = filePath.replace(/^.*[\\/]/, '');
    return fileNameWithExtension;
  }

//   function convertPly(path) {
//     fetch(path)
//     .then(function(response) {
//         return response.blob();
//     })
//     .then(function(blob) {
//         const file = new File([blob], extractFileName(path), { type: 'text/plain' });
//         selectFile(file);
//     })
//     .catch(function(error) {
//         console.error('Error fetching file:', error);
//     });
// }


function selectFile(splatData){
    console.log("start");
    //splatData = new Uint8Array(binary);
    console.log("aa")
    const rowLength = 3 * 4 + 3 * 4 + 4 + 4;
    console.log(typeof(splatData))
    console.log("Loaded", Math.floor(splatData.length / rowLength));

    if (
        splatData[0] == 112 &&
        splatData[1] == 108 &&
        splatData[2] == 121 &&
        splatData[3] == 10
    ) {
        // ply file magic header means it should be handled differently

        //worker.postMessage({ ply: splatData.buffer });
        console.log("ok");
        processPlyBuffer(splatData)
        //processPlyBuffer(splatData.buffer);
    } else {
        console.warn("unsupported file type");
    }


}
  