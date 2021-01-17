const UPLOAD_IMAGES_CHUNK_SIZE = 16; // How many images are going together in one request
const UPLOAD_IMAGES_MAX_SIZE = 512 * 1024; // 512kb
const COLUMN_MOVE_SPEED_PX = 2.5;

const encodePayload = (payload) => JSON.stringify(payload);
const decodePayload = (payload) => JSON.parse(payload);
const queuedImages = [];
let pendingRequestForMoreImages = true;

const messageHandler = (payload) => {
    const message = decodePayload(payload.data);

    if (message.type === 'more_images') {
        moreImagesHandler(message.images);
    }
};

const moreImagesHandler = (images) => {
    let finishedCounter = 0;
    for (let image of images) {
        // TODO: Possible make this async?
        LZMA.decompress(new Uint8Array(base64ToArrayBuffer(image.data)), (decompressed, error) => {
            let imageElem = new Image();
            imageElem.src = `data:image/jpeg;base64,${arrayBufferToBase64(decompressed)}`;
            imageElem.draggable = false;
            imageElem.dataset.id = image.id;
            imageElem.onload = () => {
                queuedImages.push(imageElem);
                finishedCounter++;

                if (finishedCounter === images.length) {
                    pendingRequestForMoreImages = false;
                }
            };
        });
    }

    if (images.length === 0) {
        pendingRequestForMoreImages = false;
    }
};

const ws = new WebSocket(`ws://${window.location.hostname}:8001`);
ws.onmessage = messageHandler;

const uploadImages = (imageFiles) => {
    if (imageFiles.length === 0) {
        return;
    }

    const allImagesRead = (images) => {
        fetch('/new_images/', {
            method: 'POST',
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ images })
        });

        // Used to send images over the websocket, but that was very slow due to browsers just enqueueing a lot
        //   of frames instead of immediately sending them. So now we just upload images via POST request, as any
        //   reasonable human being
        /*
        ws.send(encodePayload({
            type: 'new_images',
            images,
        }));
        */
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
let columnStates = [];

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
    // This will cause the column logic to request more images on hue change
    queuedImages.length = 0;
};

const requestMoreImages = () => {
    pendingRequestForMoreImages = true;
    ws.send(encodePayload({
        type: 'more_images',
        hue,
    }));
};

const clickImageHandler = (event) => {
    let img = event.target;

    if (!img.classList.contains('deleted')) {
        let imageElems = columnStates[img.dataset.column].imageElems;

        // If we have deleted the last image element, then immediately remove it from
        //   columns state, so that new image can be placed
        if (imageElems[imageElems.length - 1] === img) {
            imageElems.pop()
        }

        // Update the style with small animation
        img.classList.add('deleted');

        // Perform a soft delete in the database
        ws.send(encodePayload({
            type: 'delete_image',
            image: img.dataset.id,
        }));
    }
}

const appendQueuedImageToColumn = (state) => {
    // If we are out of luck and there are no images, then attempt to request more images
    //   unless there is a request already pending
    if (queuedImages.length === 0 && !pendingRequestForMoreImages) {
        requestMoreImages();
        return;
    }

    if (queuedImages.length === 0) {
        return;
    }

    // We got some images! We take the last one, and attach it to the column at the bottom of the screen
    // We do some magic with margins and paddings to align images properly
    let imageElem = queuedImages.pop();
    let columnWidth = state.columnElem.clientWidth;
    let trueImageHeight = imageElem.height * (columnWidth/imageElem.naturalWidth);

    imageElem.style.marginBottom = `-${state.paddingBottom + trueImageHeight - 2}px`;
    imageElem.dataset.column = state.column;
    imageElem.onclick = clickImageHandler;
    state.imageElems.push(imageElem);
    state.columnElem.appendChild(imageElem);
};

const columnLogic = () => {
    for (let state of columnStates) {
        // First we move column upwards
        state.columnElem.style.paddingBottom = `${state.paddingBottom}px`;
        state.paddingBottom += COLUMN_MOVE_SPEED_PX;

        // Next we check if the column does not have any images, so we try to add one of the queued
        //   queued images to the column
        if (state.imageElems.length === 0) {
            appendQueuedImageToColumn(state);
            continue;
        }

        // We do have images in the column!

        let bottomImage = state.imageElems[state.imageElems.length - 1];
        let bottomPos = document.body.clientHeight - (state.paddingBottom + +bottomImage.style.marginBottom.replace('px', ''));
        let topImage = state.imageElems[0];

        // If bottom image is fully on the page, then we add more images to the column
        if (bottomPos <= document.body.clientHeight) {
            appendQueuedImageToColumn(state);
        }

        // If the top image is fully out of the page then we delete the element
        if (topImage.y <= -topImage.height) {
            topImage.parentNode.removeChild(topImage);
            state.imageElems.shift();
        }
    }

    // We have to manually clean up deleted images when they are out of the view, since deleted pictures
    //   are detached from columns and therefore do not get updated.
    for (let deleted of document.getElementsByClassName('deleted')) {
        if (deleted.y < -deleted.height) {
            deleted.parentNode.removeChild(deleted);
        }
    }
};

window.onload = () => {
    inputOverlay = window.document.body;
    dropArea = document.getElementById('drop-area');
    hueSelector = document.getElementById('hue-selector');

    let colElems = document.getElementsByClassName('image-column');
    for (let i = 0; i < 4; i++) {
        columnStates.push({
            columnElem: colElems[i],
            imageElems: [], // Top-to-bottom
            paddingBottom: 0,
            column: i,
        });
    }

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

    // Makes things move
    setInterval(columnLogic, 40)
};

