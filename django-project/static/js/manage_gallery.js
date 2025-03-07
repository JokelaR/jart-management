const addMediaButton = document.getElementById('addMedia');
const addEmbedButton = document.getElementById('addEmbed');
const mediaTemplate = document.getElementById('new-image-template');
const tagTemplate = document.getElementById('tag-template');
const autocompleteTemplate = document.getElementById('autocomplete-template');
const galleryTitleTemplate = document.getElementById('gallery-title-template');
const editableTitleTemplate = document.getElementById('editable-title-template');
const listContainer = document.getElementById('listContainer');
const galleryTitleElement = document.getElementById('galleryTitle');
const galleryCategorySelect = document.getElementById('galleryCategory');
const galleryVisibilitySelect = document.getElementById('galleryVisibility');
const galleryDateElement = document.getElementById('galleryDate');

const allowedImageTypes = ['image/png', 'image/jpeg', 'image/webp', 'image/apng', 'image/avif', 'image/gif']
const allowedVideoTypes = ['video/mp4', 'video/webm', 'video/ogg']

const localStorage = window.localStorage;

let order_changed = false;
let items_changed = false;
//TODO show the order status in the toolbar

galleryCategorySelect.value = original_category;
let currentCategory = galleryCategorySelect.value;

galleryCategorySelect.addEventListener('change', update_category);
galleryVisibilitySelect.addEventListener('change', update_visibility);
galleryDateElement.addEventListener('change', update_date);

media_items.forEach(media_item => {
    append_media_template(media_item['src'], media_item['title'], media_item['creator_tags'], media_item['tags'], media_item['description'], media_item['uploaderDescription'], media_item['loop'], media_item['uuid'], media_item['type'], 'saved');
});

function prepareMedia(file) {
    return new Promise((resolve, reject) => {
        if (allowedImageTypes.includes(file.type)) {
            let fileurl = URL.createObjectURL(file)
            let img = new Image();
            img.onload = () => {
                if (img.width == 0 || img.height == 0) {
                    toast(`${file.name} has a zero for height or width! Screenshot this for Bulder`, -1, 'warn');
                    reject();
                }
                let height = img.height;
                let width = img.width;

                URL.revokeObjectURL(fileurl);
                console.log('Resolved', file.name);
                resolve({'file': file, 'height': height, 'width': width, 'type': file.type});
            }
            img.src = fileurl;
        }
        else if (allowedVideoTypes.includes(file.type)) {
            let fileurl = URL.createObjectURL(file)
            let videoElement = document.createElement('video');
            videoElement.preload = 'metadata';
            videoElement.onloadedmetadata = function() {
                if(videoElement.videoWidth == 0 || videoElement.videoHeight == 0) {
                    toast(`${file.name} has a zero for height or width! Screenshot this for Bulder`, -1, 'warn');
                }
                let height = videoElement.videoHeight;
                let width = videoElement.videoWidth;

                URL.revokeObjectURL(fileurl);
                console.log('Resolved', file.name);
                resolve({'file': file, 'height': height, 'width': width, 'type': file.type});
            }
            videoElement.src = fileurl;
        }
        else {
            toast(`${file.type} is not a supported file type`, 4000, 'error');
        }
    });
}

async function createMedia(mediaObject) {
    let fd = new FormData();
    fd.append('csrfmiddlewaretoken', csrf_token);

    fd.append('file', mediaObject.file);
    fd.append('type', mediaObject.type);
    fd.append('width', mediaObject.width);
    fd.append('height', mediaObject.height);
    fd.append('loop', false);

    let request = new Request('/create/media', { method: "POST", body: fd });
    return new Promise((resolve, reject) => {
        fetch(request).then((response) => { response.json().then((data) => {
            if(data['url']) {
                console.log('Created', data['url']);
                resolve({'uuid': data['uuid'], 'url': data['url'], 'type': mediaObject.type});
            }
            else {
                reject(mediaObject.file.name);
            }
        })});
    });
}



//Add New Media
addMediaButton.addEventListener("click", (event) => {
    let input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;

    let fd = new FormData();
    fd.append('csrfmiddlewaretoken', csrf_token);

    input.onchange = (e) => {
        let filePromises = [];
        filePromises.length = e.target.files.length;

        for (let index = 0; index < e.target.files.length; index++) {
            const file = e.target.files[index];
            filePromises[index] = prepareMedia(file);
        }

        Promise.allSettled(filePromises).then((mediaObjects) => {
            console.log(mediaObjects);
            let createPromises = [];
            
            for (let index = 0; index < mediaObjects.length; index++) {
                const mediaObject = mediaObjects[index];
                if (mediaObject.status == 'fulfilled') {
                    createPromises.push(createMedia(mediaObject.value));
                }
            }

            Promise.allSettled(createPromises).then((responses) => {
                console.log(responses);
                responses.forEach((fileInfo) => {
                    if (fileInfo.status == 'fulfilled')
                    {
                        info = fileInfo.value;
                        append_media_template(mediaPath + info.url, '', '', '', '', '', false, info.uuid, info.type, 'changed');
                    }
                    else {
                        toast(`Failed to add ${fileInfo.reason}`, 4000, 'error');
                    }
                });
                save_gallery();
            });
        });
    }
    input.click();
});

addEmbedButton.addEventListener("click", (event) => {
    let embed = window.prompt("Enter the YouTube url in the format https://www.youtube.com/watch?v=[ID], with nothing after the ID");
    if(embed && embed != '' && embed.includes('https://www.youtube.com/watch?v=')) {
        let fd = new FormData();
        fd.append('csrfmiddlewaretoken', csrf_token);
        fd.append('url', 'https://www.youtube-nocookie.com/embed/' + embed.substring(embed.indexOf('=') + 1));

        fd.append('type', 'embed');
        fd.append('width', 1280);
        fd.append('height', 720);
        fd.append('loop', false);


        let request = new Request('/create/mediaEmbed', { method: "POST", body: fd });
        fetch(request).then((response) => { response.json().then((data) => {
            toastResult(response, 'Created embed', 'Failed to create embed');
            if(data['url']) {
                append_media_template(data['url'], '', '', '', '', '', false, data['uuid'], 'embed', 'changed');
                update_gallery_order();
            }
        })});
    }
    else {
        toast('Invalid Youtube URL (we only support the https://www.youtube.com/watch?v=[ID] format right now)', 4000, 'error');
    }
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

/**
 * Appends a media template to the list container with the provided data.
 * 
 * @param {string} url - Media URL.
 * @param {string} title
 * @param {string[]} creator_tags
 * @param {Object[]} tags
 * @param {string} description
 * @param {string} extra_description - Uploader description.
 * @param {string} loop - "True" or "False"
 * @param {string} uuid
 * @param {string} type
 * @param {string} current_status - "changed", "saving", or "saved"
 */
function append_media_template(url, title, creator_tags, tags, description, extra_description, loop, uuid, type, current_status) {
    let template_clone = mediaTemplate.content.cloneNode(true);
    let new_node;
    if (type == 'embed') {
        new_node = document.createElement('p');
        new_node.textContent = '🔗';
    }
    else if(allowedImageTypes.includes(type)) {
        new_node = document.createElement('img');
        new_node.src = url;
        new_node.loading = 'lazy';
        new_node.title = url.replace('/media/', '');

        let overlay = document.createElement('img');
        overlay.src = url;
        overlay.loading = 'lazy';
        template_clone.querySelector('.previewOverlay').appendChild(overlay);
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
    template_clone.querySelector('.mediaElement').addEventListener('change', on_media_updated);
    template_clone.querySelector('.mediaElement').dataset.status = current_status;
    template_clone.querySelector('button[name="up"]').addEventListener('click', move_media_item_up);
    template_clone.querySelector('.orderInput').value = listContainer.children.length + 1;
    template_clone.querySelector('.orderInput').addEventListener('change', move_media_item);
    template_clone.querySelector('button[name="down"]').addEventListener('click', move_media_item_down);
    template_clone.querySelector('button[name="collapse"]').addEventListener('click', collapse_media);
    let form = template_clone.querySelector('form');
    form['title'].value = title;

    attach_autocomplete(form['creator_tags'], 'creator');
    for (let index = 0; index < creator_tags.length; index++) {
        let tag_clone = tagTemplate.content.cloneNode(true);
        tag_clone.querySelector('.tagLabel').textContent = creator_tags[index];
        tag_clone.querySelector('.tag').dataset.tagNamespace = 'creator';
        tag_clone.querySelector('.tag').dataset.tagname = creator_tags[index];
        form['creator_tags'].parentElement.insertBefore(tag_clone, form['creator_tags']);
    }

    attach_autocomplete(form['tags']);
    for (let index = 0; index < tags.length; index++) {
        let tag_clone = tagTemplate.content.cloneNode(true);
        tag_clone.querySelector('.tagLabel').textContent = tags[index].tagname;
        tag_clone.querySelector('.tag').dataset.tagNamespace = tags[index].namespace;
        tag_clone.querySelector('.tag').dataset.tagname = tags[index].tagname;
        form['tags'].parentElement.insertBefore(tag_clone, form['tags']);
    }

    form['description'].textContent = description;
    form['uploaderDescription'].textContent = extra_description;
    form['uuid'].value = uuid;
    form['delete'].addEventListener('click', delete_media_button);
    form['loop'].checked = (loop == true || loop == 'True') 

    if (localStorage.getItem(`media_${uuid}_collapsed`) == 'true') {
        template_clone.querySelector('.mediaElement').classList.add('collapsed');
    }

    listContainer.append(template_clone);
    order_changed = true;
}

function collapse_media(event) {
    let media_element = event.target.closest('.mediaElement');

    let id = media_element.querySelector('form')['uuid'].value;
    if (!media_element.classList.contains('collapsed')) {
        localStorage.setItem(`media_${id}_collapsed`, 'true');
    }
    else {
        localStorage.removeItem(`media_${id}_collapsed`);
    }
    
    media_element.classList.toggle('collapsed');
}

function move_media_item(event) {
    event.stopPropagation();
    let media_element = event.target.closest('.mediaElement');
    let media_list = media_element.parentNode;
    let target = Math.max(parseInt(event.target.value), 0);
    if (target > media_list.children.length) {
        target = media_list.children.length - 1;
    }
    else if (target == 1) {
        target = 0;
    }
    media_list.insertBefore(media_element, media_list.children[target]);
    refresh_indeces();
}
function move_media_item_up(event) {
    let media_element = event.target.closest('.mediaElement');
    let media_list = media_element.parentNode;
    media_list.insertBefore(media_element, media_element.previousElementSibling);
    order_changed = true;
    refresh_indeces();
}
function move_media_item_down(event) {
    let media_element = event.target.closest('.mediaElement');
    let media_list = media_element.parentNode;
    media_list.insertBefore(media_element, media_element.nextElementSibling.nextElementSibling);
    order_changed = true;
    refresh_indeces();
}

function refresh_indeces() {
    let elements = listContainer.querySelectorAll('.orderInput');
    for (let index = 0; index < elements.length; index++) {
        const element = elements[index];
        element.value = index + 1;
    }
}

function save_gallery() {
    let changed_images = listContainer.querySelectorAll('.mediaElement[data-status="changed"]');
    for (let index = 0; index < changed_images.length; index++) {
        let media_element = changed_images[index];
        media_element.dataset.status = 'saving';
        let form = media_element.querySelector('form');

        let fd = new FormData(form);

        let tags = [];
        let tagElements = form['tags'].parentElement.querySelectorAll('.tag')
        for (let index = 0; index < tagElements.length; index++) {
            const tag = tagElements[index];
            if (tag.dataset.tagNamespace != undefined) {
                tags.push({ 
                    'namespace': tag.dataset.tagNamespace, 
                    'tagname': tag.dataset.tagname 
                });    
            }
            else {
                tags.push({ 
                    'namespace': '', 
                    'tagname': tag.dataset.tagname
                });    
            }
        }

        let creator_tags = [];
        let creatorTagElements = form['creator_tags'].parentElement.querySelectorAll('.tag')
        for (let index = 0; index < creatorTagElements.length; index++) {
            const tag = creatorTagElements[index];
            creator_tags.push({ 
                'namespace': 'creator', 
                'tagname': tag.dataset.tagname 
            });
        }

        fd.append('tags', JSON.stringify(tags));
        fd.append('creator_tags', JSON.stringify(creator_tags));
        try {
            let request = new Request('/modify/media', { 
                method: "POST", 
                body: fd, 
                headers: { 'X-CSRFToken': csrf_token }
            });
            fetch(request).then((response) => {
                if(response.status == 200) {
                    media_element.dataset.status = 'saved';
                }
                else {
                    media_element.dataset.status = 'changed';
                }
                toastResult(response, 'Saved media changes!', 'Failed to save media changes');
            });
        } catch (error) {
            media_element.dataset.status = 'changed';
            toast('Unknown network failure when saving media.', 4000, 'error');
        }
    }
    if (order_changed) {
        update_gallery_order();
    }
}

function update_gallery_order() {
    let images = [];
    elements = listContainer.querySelectorAll('form');
    for (let index = 0; index < elements.length; index++) {
        const element = elements[index];
        images.push(element['uuid'].value);
    }

    let request = new Request(`/modify/gallery/${gallery_id}/media`, {
        method: "POST",
        body: images.toString(),
        headers: { 'X-CSRFToken': csrf_token }
    });
    fetch(request).then((response) => {
        if(response.status == 200) {
            order_changed = false;
        }
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

function update_category() {
    let newCategory = galleryCategorySelect.value;
    if(newCategory != currentCategory) {
        if(newCategory == 'new') {
            newCategory = window.prompt("New category (all lowercase, underscores for spaces):");
            if(newCategory) {
                let newCategoryElement = document.createElement('option');
                newCategoryElement.value = newCategory;
                newCategoryElement.textContent = newCategory;
                galleryCategorySelect.insertBefore(newCategoryElement, galleryCategorySelect.lastElementChild);
            }
            else {
                galleryCategorySelect.value = currentCategory;
                return;
            }
        }
        let request = new Request(`/modify/gallery/${gallery_id}/category`, {
            method: "POST",
            body: newCategory,
            headers: { 'X-CSRFToken': csrf_token }
        })
        fetch(request).then((response) => {
            toastResult(response, 'Updated category!', 'Failed to update category');
            if(response.status == 200) {
                currentCategory = newCategory;
            }
            galleryCategorySelect.value = currentCategory;
        });
    }
}

function update_visibility() {
    let visibility = galleryVisibilitySelect.value;
    let request = new Request(`/modify/gallery/${gallery_id}/visibility`, {
        method: "POST",
        body: visibility,
        headers: { 'X-CSRFToken': csrf_token }
    });
    fetch(request).then((response) => {
        toastResult(response, 'Updated visibility!', 'Failed to update visibility');
    });
}

function update_date() {
    let date = galleryDateElement.value;
    let request = new Request(`/modify/gallery/${gallery_id}/date`, {
        method: "POST",
        body: date,
        headers: { 'X-CSRFToken': csrf_token }
    });
    fetch(request).then((response) => {
        toastResult(response, 'Updated date!', 'Failed to update date');
    });
}

async function associate_media(uuid, order) {
    let request = new Request(`/modify/gallery/${gallery_id}/associate_media`, {
        method: "POST",
        body: [uuid, order].toString(),
        headers: { 'X-CSRFToken': csrf_token }
    })
    await fetch(request).then((response) => {
        console.log('Associated', uuid);
        toastResult(response, 'Linked media to gallery', 'Media link failed');
    });
}


let autocomplete_list = undefined;
let autocomplete_data = null;
function attach_autocomplete(element, target_namespace) {
    if(target_namespace != undefined) {
        element.dataset.namespace = target_namespace;
    }

    element.addEventListener('input', debounce(async function(event) {
        if(autocomplete_list == undefined) {
            event.target.parentElement.appendChild(autocompleteTemplate.content.cloneNode(true));
            autocomplete_list = event.target.parentElement.querySelector('.autocompletePopup');
        }
        let list_element = autocomplete_list.querySelector('ul');
        list_element.innerHTML = '';

        let tag = event.target.value;
        let namespace = event.target.dataset.namespace;

        if(namespace == undefined && tag.includes(':')) {
            namespace = tag.split(':')[0];
            tag = tag.replace(namespace + ':', '');
        }
        else if (namespace == undefined) {
            namespace = '';
        }

        let request_data = { 'incomplete_tag': tag, 'namespace': namespace }
        let request = new Request('/tags/autocomplete/', {
            method: "POST",
            body: JSON.stringify(request_data),
            content_type: "application/json",
            headers: { 'X-CSRFToken': csrf_token }
        });

        const response = await fetch(request);
        const data = await response.json();

        autocomplete_data = data.tags;

        if(autocomplete_data.length == 0) {
            hideAutocomplete();
        }
        else {
            for (let i = 0; i < data.tags.length; i++) {
                const tag = data.tags[i];
                let suggestion = document.createElement('li');
                if (namespace == '') {
                    suggestion.textContent = `${tag.namespace}:${tag.tagname}`;
                }
                else {
                    suggestion.textContent = tag.tagname;
                }
                suggestion.addEventListener('click', function() {
                    add_tag(event.target, tag.namespace, tag.tagname);
                    event.target.value = '';
                    hideAutocomplete();
                });
                list_element.appendChild(suggestion);
            }
        }
    }, 250));
    element.parentElement.addEventListener('focusout', function() {
        settimeout = setTimeout(hideAutocomplete, 100);
    });
    element.addEventListener('keydown', function(event) {
        if (event.target.value != '') {
            if(event.key == 'Enter') {
                event.preventDefault();
                let tag = event.target.value;
                let namespace = event.target.dataset.namespace;
    
                if (namespace == undefined && tag.includes(':')) {
                    namespace = tag.split(':')[0];
                    tag = tag.replace(namespace + ':', '');
                }
                if(tag != '') {
                    add_tag(event.target, namespace, tag);
                    event.target.value = '';
                    hideAutocomplete();    
                }
            }
            if (event.key == 'Tab') {
                event.preventDefault();
                if(autocomplete_data.length > 0) {
                    add_tag(event.target, autocomplete_data[0].namespace, autocomplete_data[0].tagname);
                    event.target.value = '';
                    hideAutocomplete();
                }
            }    
        }
        if (event.key == 'Backspace' && event.target.value == '') {
            event.preventDefault();
            if(event.target.previousElementSibling) {
                event.target.previousElementSibling.remove();
                event.target.dispatchEvent(new Event('change', { bubbles: true }));
            }
            hideAutocomplete();
        }
    });
}

function hideAutocomplete() {
    if(autocomplete_list != undefined) {
        autocomplete_list.remove();
        autocomplete_data = undefined;
        autocomplete_list = undefined;
    }
}

function add_tag(beforeTarget, namespace, tagname) {
    let tag_clone = tagTemplate.content.cloneNode(true);
    tag_clone.querySelector('.tagLabel').textContent = tagname.trim();
    if (namespace == undefined) { namespace = ''; }
    tag_clone.querySelector('.tag').dataset.tagNamespace = namespace.trim();
    tag_clone.querySelector('.tag').dataset.tagname = tagname.trim();
    beforeTarget.parentElement.insertBefore(tag_clone, beforeTarget);
    beforeTarget.dispatchEvent(new Event('change', { bubbles: true }));
}

function remove_tag(source) {
    source.dispatchEvent(new Event('change', { bubbles: true }));
    source.remove();
}

function on_media_updated(event) {
    event.currentTarget.dataset.status = 'changed';
}

function toastResult(response, successText, failureText) {
    if(!successText) { successText = 'Success!'; }
    if(!failureText) { failureText = 'Failed'}
    if(response.status == 200) {
        toast(successText, 4000, 'info');
    }
    else {
        toast(`${failureText} (${response.statusText})`, 4000, 'error')
    }
}

function toast(text, duration, severity) {
    switch (severity) {
        case 'info':
            Toastify({
                text: text,
                duration: duration
            }).showToast();
            break;
        case 'warn':
            Toastify({
                text: text,
                duration: -1,
                close: true,
                style: {
                    background: 'gold'
                }
            }).showToast();
        case 'error':
            Toastify({
                text: text,
                duration: -1,
                close: true,
                style: {
                    background: 'darkred'
                }
            }).showToast();
        default:
            break;
    }
} 

function debounce(callback, wait) {
    let timeout;
    return (...args) => {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => callback.apply(context, args), wait);
    };
}