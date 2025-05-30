/*!
* Start Bootstrap - SB Admin Pro v2.0.5 (https://shop.startbootstrap.com/product/sb-admin-pro)
* Copyright 2013-2023 Start Bootstrap
* Licensed under SEE_LICENSE (https://github.com/StartBootstrap/sb-admin-pro/blob/master/LICENSE)
*/

window.addEventListener('DOMContentLoaded', event => {
    console.log("✅ script.js is loaded!");
    console.log("✅ scripts.js from project is REALLY LOADED");

    // Activate feather
    feather.replace();

    // Enable tooltips globally
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enable popovers globally
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Toggle the side navigation
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        // Uncomment Below to persist sidebar toggle between refreshes
        // if (localStorage.getItem('sb|sidebar-toggle') === 'true') {
        //     document.body.classList.toggle('sidenav-toggled');
        // }
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sidenav-toggled'));
        });
    }

    // Close side navigation when width < LG
    const sidenavContent = document.body.querySelector('#layoutSidenav_content');
    if (sidenavContent) {
        sidenavContent.addEventListener('click', event => {
            const BOOTSTRAP_LG_WIDTH = 992;
            if (window.innerWidth >= 992) {
                return;
            }
            if (document.body.classList.contains("sidenav-toggled")) {
                document.body.classList.toggle("sidenav-toggled");
            }
        });
    }

    // Add active state to sidbar nav links
    let activatedPath = window.location.pathname.match(/([\w-]+\.html)/, '$1');

    if (activatedPath) {
        activatedPath = activatedPath[0];
    } else {
        activatedPath = 'index.html';
    }

    const targetAnchors = document.body.querySelectorAll('[href="' + activatedPath + '"].nav-link');

    targetAnchors.forEach(targetAnchor => {
        let parentNode = targetAnchor.parentNode;
        while (parentNode !== null && parentNode !== document.documentElement) {
            if (parentNode.classList.contains('collapse')) {
                parentNode.classList.add('show');
                const parentNavLink = document.body.querySelector(
                    '[data-bs-target="#' + parentNode.id + '"]'
                );
                parentNavLink.classList.remove('collapsed');
                parentNavLink.classList.add('active');
            }
            parentNode = parentNode.parentNode;
        }
        targetAnchor.classList.add('active');
    });

    const fileInput = document.getElementById('imageInput');
    const form = document.getElementById('profileImageForm');

    if (fileInput && form) {
        fileInput.addEventListener('change', function () {
            if (fileInput.files.length > 0) {
                form.submit();
            }
        });
    }

    const deleteButtons = document.querySelectorAll('.open-delete-modal');
    const modalItemName = document.getElementById('modalItemName');
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    const deleteForm = document.getElementById('deleteForm');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function () {
            const name = this.getAttribute('data-name') || this.getAttribute('data-title');
            const url = this.getAttribute('data-url');
            const usePost = this.getAttribute('data-method') === 'post';

            console.log("🗑️ Öppnar modal för:", name);
            if (modalItemName) modalItemName.textContent = name || '[Okänt]';

            if (usePost) {
                if (deleteForm) {
                    deleteForm.action = url;
                    deleteForm.style.display = 'inline-block';
                }
                if (confirmBtn) confirmBtn.style.display = 'none';
            } else {
                if (confirmBtn) {
                    confirmBtn.href = url;
                    confirmBtn.style.display = 'inline-block';
                }
                if (deleteForm) deleteForm.style.display = 'none';
            }
        });
    });
});