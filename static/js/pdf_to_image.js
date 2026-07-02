
// Generate or retrieve a persistent job_id for this user/tab
let jobId = sessionStorage.getItem('pdf_converter_job_id');
if (!jobId) {
    jobId = crypto.randomUUID ? crypto.randomUUID() : ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c => (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16));
    sessionStorage.setItem('pdf_converter_job_id', jobId);
}

const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileNameSpan = document.getElementById('fileName');
const fileSizeSpan = document.getElementById('fileSize');
const dropzone = document.getElementById('dropzone');
const convertBtn = document.getElementById('convertBtn');
const messageArea = document.getElementById('messageArea');
const galleryArea = document.getElementById('galleryArea');
const qualitySelect = document.getElementById('qualitySelect');
const formatSelect = document.getElementById('formatSelect');

// File selection preview
fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
        const f = fileInput.files[0];
        fileInfo.classList.remove('hidden');
        fileNameSpan.textContent = f.name;
        fileSizeSpan.textContent = (f.size / 1024 / 1024).toFixed(2) + ' MB';
    }
});

document.getElementById('removeFile').onclick = () => {
    fileInput.value = '';
    fileInfo.classList.add('hidden');
};

dropzone.addEventListener('click', (e) => {
    if (e.target === dropzone) fileInput.click();
});

// Show temporary message (still uses simple div)
function showMessage(msg, type) {
    const colors = {
        error: 'bg-red-50 border-red-200 text-red-800',
        success: 'bg-green-50 border-green-200 text-green-800',
        info: 'bg-blue-50 border-blue-200 text-blue-800'
    };
    messageArea.innerHTML = `<div class="mt-6 p-4 rounded-xl border text-sm ${colors[type] || colors.info}">${msg}</div>`;
    if (type === 'error') {
        setTimeout(() => {
            if (messageArea.firstChild?.innerText === msg) messageArea.innerHTML = '';
        }, 5000);
    }
}

// Render image gallery
function updateGallery(images, jobId) {
    if (!images?.length) {
        galleryArea.innerHTML = '';
        return;
    }

    const downloadUrl = `/download-zip?job_id=${encodeURIComponent(jobId)}`;
    let html = `
        <div class="mt-12 border-t pt-8">
            <div class="flex justify-between items-center mb-6">
                <h3 class="font-semibold text-gray-800">Converted Images (${images.length})</h3>
                <a href="${downloadUrl}" class="px-4 py-2 bg-black text-white rounded-lg text-sm hover:bg-gray-800 transition">
                    Download ZIP
                </a>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
    `;
    for (const img of images) {
        html += `
            <div class="bg-white border rounded-2xl overflow-hidden hover:shadow-md transition">
                <div class="p-3 bg-gray-50">
                    <img src="${img.url}" class="rounded-xl max-h-56 mx-auto">
                </div>
                <div class="px-4 py-3 flex justify-between items-center">
                    <span class="text-sm text-gray-700">Page ${img.index}</span>
                    <a href="${img.url}" download class="text-indigo-600 hover:text-indigo-800">⬇</a>
                </div>
            </div>
        `;
    }
    html += `</div></div>`;
    galleryArea.innerHTML = html;
}

// AJAX conversion
convertBtn.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) {
        showMessage('Please select a PDF file first.', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('job_id', jobId);
    formData.append('file', file);
    formData.append('quality', qualitySelect.value);
    formData.append('format', formatSelect.value);

    convertBtn.disabled = true;
    convertBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Converting...';
    showMessage('Converting PDF, please wait...', 'info');

    try {
        const response = await fetch('/', {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await response.json();

        if (response.ok && data.success) {
            showMessage(data.message, 'success');
            updateGallery(data.images, data.job_id);
            // Auto‑cleanup after 1 hour
            setTimeout(() => {
                fetch('/cleanup', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: `job_id=${encodeURIComponent(jobId)}` });
                sessionStorage.removeItem('pdf_converter_job_id');
            }, 3600000);
        } else {
            showMessage(data.error || 'Conversion failed', 'error');
        }
    } catch (err) {
        showMessage('Network error. Please try again.', 'error');
        console.error(err);
    } finally {
        convertBtn.disabled = false;
        convertBtn.innerHTML = 'Convert Now';
    }
});

// On page load, check existing images and show SweetAlert dialog
window.addEventListener('load', async () => {
    try {
        const res = await fetch(`/list-images?job_id=${encodeURIComponent(jobId)}`);
        const data = await res.json();
        if (data.success && data.images && data.images.length > 0) {
            // SweetAlert confirmation
            const result = await Swal.fire({
                title: 'Previous images found',
                text: `You have ${data.images.length} previously converted image(s). Do you want to clear them?`,
                icon: 'question',
                showCancelButton: true,
                confirmButtonText: 'Yes, clear them',
                cancelButtonText: 'No, keep them',
                reverseButtons: true
            });

            if (result.isConfirmed) {
                // User wants to clear
                await fetch('/cleanup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `job_id=${encodeURIComponent(jobId)}`
                });
                sessionStorage.removeItem('pdf_converter_job_id');
                galleryArea.innerHTML = '';
                showMessage('All data cleared. Reload the page to start fresh.', 'info');
                fileInput.value = '';
                fileInfo.classList.add('hidden');
                // Generate new jobId
                jobId = crypto.randomUUID ? crypto.randomUUID() : ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c => (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16));
                sessionStorage.setItem('pdf_converter_job_id', jobId);
            } else {
                // Keep data – display existing gallery
                updateGallery(data.images, jobId);
                showMessage(`Restored ${data.images.length} previous image(s).`, 'info');
            }
        }
    } catch (err) {
        console.warn("Could not check existing images:", err);
    }
});