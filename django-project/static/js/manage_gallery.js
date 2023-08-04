const addMediaButton = document.getElementById('addMedia');
const mediaTemplate = document.getElementById('new-image-template');
const galleryTitleTemplate = document.getElementById('gallery-title-template');
const editableTitleTemplate = document.getElementById('editable-title-template');
const listContainer = document.getElementById('listContainer');
const galleryTitleElement = document.getElementById('galleryTitle');

const allowedImageTypes = ['image/png', 'image/jpeg', 'image/webp', 'image/apng', 'image/avif', 'image/gif']
const allowedVideoTypes = ['video/mp4', 'video/webm', 'video/ogg']

media_items.forEach(media_item => {
    append_media_template(media_item['src'], media_item['author'], media_item['description'], media_item['uploaderDescription'], media_item['loop'], media_item['uuid'], media_item['type']);
});

//Add New Media
addMediaButton.addEventListener("click", (event) => {
    let input = document.createElement('input');
    input.type = 'file';

    let fd = new FormData();
    fd.append('csrfmiddlewaretoken', csrf_token);

    //TODO: support multi-upload
    input.onchange = (e) => {
        let file = e.target.files[0];
        let fileurl = URL.createObjectURL(file)
        if(allowedImageTypes.includes(file.type)) {
            let img = new Image;
            img.onload = function() {
                fd.append('file', file);
                fd.append('type', file.type);
                fd.append('width', img.width);
                fd.append('height', img.height);
                fd.append('loop', false);

                let request = new Request('/create/media', { method: "POST", body: fd });
                fetch(request).then((response) => { response.json().then((data) => {
                    toastResult(response, 'Created media', 'Failed to create media');
                    if(data['url']) {
                        associate_media(data['uuid'], listContainer.children.length);
                        append_media_template(mediaPath + data['url'], '', '', '', false, data['uuid'], file.type);
                    }
                    URL.revokeObjectURL(fileurl);
                })});
            }
            img.src = fileurl;
        }
        else if(allowedVideoTypes.includes(file.type)) {
            let videoElement = document.createElement('video');
            videoElement.preload = 'metadata';
            videoElement.src = fileurl;
            videoElement.onloadedmetadata = function() {
                fd.append('file', file);
                fd.append('type', file.type);
                fd.append('width', videoElement.videoWidth);
                fd.append('height', videoElement.videoHeight);
                fd.append('loop', false);                
                let request = new Request('/create/media', { method: "POST", body: fd });
                fetch(request).then((response) => { response.json().then((data) => {
                    toastResult(response, 'Created media', 'Failed to create media');
                    if(data['url']) {
                        associate_media(data['uuid'], listContainer.children.length);
                        append_media_template(mediaPath + data['url'], '', '', '', false, data['uuid'], file.type);
                    }
                    URL.revokeObjectURL(fileurl);
                })});
            }
            
        }
        else {
            Toastify({
                text: `Type '${file.type}' file not supported`,
                duration: 4000,
                style: {
                    background: 'darkred',
                }
            }).showToast();
        }
    }
    input.click();
});

function delete_media_button(event) {
    let id = event.target.form['uuid'].value;
    let request = new Request('/modify/media', { 
        method: "DELETE", 
        body: id, 
        headers: { 'X-CSRFToken': csrf_token }
    });
    fetch(request).then((response) => {
        toastResult(response, 'Deleted file', 'Failed to delete file');
        if (response.status == 200) {
            event.target.form.parentElement.remove()
        }
    });
}

function append_media_template(url, author, description, extra_description, loop, uuid, type) {
    let template_clone = mediaTemplate.content.cloneNode(true);
    let new_node;
    if(allowedImageTypes.includes(type)) {
        new_node = document.createElement('img');
        new_node.src = url;
    }
    else if(allowedVideoTypes.includes(type)) {
        new_node = document.createElement('video');
        if (loop) {
            new_node.loop = loop;
        }
        new_node.src = url;
        new_node.controls = true;
    }
    else {
        new_node = document.createElement('p');
        new_node.textContent = url;
    }
    template_clone.querySelector('.imageContainer').replaceChild(new_node, template_clone.getElementById('replaceme'))
    template_clone.querySelector('button[name="up"]').addEventListener('click', move_media_item_up);
    template_clone.querySelector('button[name="down"]').addEventListener('click', move_media_item_down);
    let form = template_clone.querySelector('form');
    form['author'].value = author;
    form['description'].textContent = description;
    form['uploaderDescription'].textContent = extra_description;
    form['uuid'].value = uuid;
    form['delete'].addEventListener('click', delete_media_button);
    form['loop'].checked = (loop == true || loop == 'True') 
    listContainer.append(template_clone);
}

function move_media_item_up(event) {
    let media_element = event.target.parentElement.parentElement;
    media_list = media_element.parentNode;
    media_list.insertBefore(media_element, media_element.previousElementSibling);
}
function move_media_item_down(event) {
    let media_element = event.target.parentElement.parentElement;
    media_list = media_element.parentNode;
    media_list.insertBefore(media_element, media_element.nextElementSibling.nextElementSibling);
}

function save_gallery() {
    let images = []
    for (let index = 0; index < listContainer.children.length; index++) {
        let form = listContainer.children[index].querySelector('form');
        images.push(form['uuid'].value)

        let fd = new FormData(form);
        let request = new Request('/modify/media', { 
            method: "POST", 
            body: fd, 
            headers: { 'X-CSRFToken': csrf_token }
        });
        fetch(request).then((response) => {
            toastResult(response, 'Saved media changes!', 'Failed to media changes');
        });
    }
    let request = new Request(`/modify/gallery/${gallery_id}/media`, {
        method: "POST",
        body: images.toString(),
        headers: { 'X-CSRFToken': csrf_token }
    })
    fetch(request).then((response) => {
        toastResult(response, 'Saved media order!', 'Failed to save media order');
    });
}

let editing = false;
function edit_title() {
    if(!editing) {
        editing = true;
        galleryTitleElement.innerHTML = '';
        galleryTitleElement.append(editableTitleTemplate.content.cloneNode(true));
        galleryTitleElement.children[0].value = gallery_title;
    }
    else {
        editing = false;
        galleryTitleElement.innerHTML = '';
        galleryTitleElement.append(galleryTitleTemplate.content.cloneNode(true));
        galleryTitleElement.children[0].textContent = gallery_title;
    }
}

function update_title() {
    if(gallery_title != galleryTitleElement.children[0].value) {
        let request = new Request(`/modify/gallery/${gallery_id}/title`, {
            method: "POST",
            body: galleryTitle.children[0].value,
            headers: { 'X-CSRFToken': csrf_token }
        })
        fetch(request).then((response) => {
            gallery_title = galleryTitle.children[0].value;
            toastResult(response, 'Updated title!', 'Failed to update title');
            edit_title();
        });
    }
    else {
        edit_title();
    }
}

function associate_media(uuid, order) {
    let request = new Request(`/modify/gallery/${gallery_id}/associate_media`, {
        method: "POST",
        body: [uuid, order].toString(),
        headers: { 'X-CSRFToken': csrf_token }
    })
    fetch(request).then((response) => {
        toastResult(response, 'Linked media right!', 'Media link failed');
    });
}

function toastResult(response, successText, failureText) {
    if(!successText) { successText = 'Success!'; }
    if(!failureText) { failureText = 'Failed'}
    if(response.status == 200) {
        Toastify({
            text: successText,
            duration: 4000
        }).showToast();
    }
    else {
        Toastify({
            text: `${failureText} (${response.statusText})`,
            duration: 4000
        }).showToast();    
    }
}