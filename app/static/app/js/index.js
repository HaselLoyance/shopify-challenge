const UPLOAD_IMAGES_CHUNK_SIZE = 16; // How many images are going together in one request
const UPLOAD_IMAGES_MAX_SIZE = 512 * 1024; // 512kb

const encodePayload = (payload) => JSON.stringify(payload);
const decodePayload = (payload) => JSON.parse(payload);

const messageHandler = (payload) => {
    const message = decodePayload(payload.data);

    if (message.type === 'more_images') {
        moreImagesHandler(message.images);
    }
};

const moreImagesHandler = (images) => {
   var element = document.getElementsByTagName("img"), index;

    for (index = element.length - 1; index >= 0; index--) {
            element[index].parentNode.removeChild(element[index]);
        
    }
    // TODO: Some advanced algorithm for placing images. Oh and also they should move. And we should have soft deletes
    for (let image of images) {
        // TODO: Possible make this async?
        let decompressed = LZMA.decompress(new Uint8Array(base64ToArrayBuffer(image.data)));
        let imageBase64 = arrayBufferToBase64(decompressed);
        let imageElem = new Image();

        imageElem.src = `data:image/jpeg;base64,${imageBase64}`;
        document.body.appendChild(imageElem);
    }
};

const ws = new WebSocket(`ws://${window.location.hostname}:8001`);
ws.onmessage = messageHandler;

const uploadImages = (imageFiles) => {
    if (imageFiles.length === 0) {
        return;
    }

    const allImagesRead = (images) => {
        console.log('batch sent')
        fetch('/new_images/', {
            method: 'POST',
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
                            
            },
            body: JSON.stringify({ images })
        });
        /*
        ws.send(encodePayload({
            type: 'new_images',
            images,
        }));


        console.log(ws.bufferedAmount)*/
    };

    let images = [];
    for (let file of imageFiles) {
        let reader = new FileReader()
        reader.readAsDataURL(file)
        reader.onloadend = () => {
            images.push(reader.result.split(',')[1]);
            if (images.length === imageFiles.length) {
                allImagesRead(images);
            }
        };
    }
};

let dropArea = null;
let inpurtOverlay = null;
let hueSelector = null;
let hue = 0;

const dragEnterHandler = (event) => {
    if (event.fromElement === null) {
        dropArea.classList.add('active');
    }
};

const dragLeaveHandler = (event) => {
    if (event.fromElement === null) {
        dropArea.classList.remove('active');
    }
};

const dropHandler = (event) => {
    dropArea.classList.remove('active');

    let files = event.dataTransfer.files;
    let fileChunks = [];

    // Separate all files to upload into several chunks. Also, check file extension to only accept
    //   images. And also limit the input files by size
    for (let i = 0; i < files.length; i++) {
        let file = files[i];

        if ((!file.name.endsWith('.png') && !file.name.endsWith('.jpg') && !file.name.endsWith('.jpeg')) || file.size > UPLOAD_IMAGES_MAX_SIZE) {
            continue;
        }

        // Chunk splitting
        if (i === 0 || i % UPLOAD_IMAGES_CHUNK_SIZE === 0) {
            fileChunks.push([]);
        }

        fileChunks[fileChunks.length - 1].push(files[i]);
    }

    fileChunks.forEach(uploadImages);
};

const hueInputHandler = (event) => {
    hue = event.target.value;
    document.body.style.backgroundColor = `hsl(${hue/255.0*360.0},90%,60%)`; 
};


const hueChangeHandler = (event) => {
    // Get more images with this hue
    ws.send(encodePayload({
        type: 'more_images',
        hue,
    }));
};



window.onload = () => {
    inputOverlay = window.document.body;
    dropArea = document.getElementById('drop-area');
    hueSelector = document.getElementById('hue-selector');

    // Handle changing the hue
    hueSelector.addEventListener('input', hueInputHandler, false);
    hueSelector.addEventListener('change', hueChangeHandler, false);

    // Prevent propogration for these events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(name => {
        inputOverlay.addEventListener(name, (event) => {
            event.preventDefault();
            event.stopPropagation();
        }, false);
    });

    inputOverlay.addEventListener('dragenter', dragEnterHandler, false);
    inputOverlay.addEventListener('dragleave', dragLeaveHandler, false);
    inputOverlay.addEventListener('drop', dropHandler, false);
};

