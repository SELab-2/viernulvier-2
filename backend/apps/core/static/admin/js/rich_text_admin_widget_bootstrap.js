/*
 * Rich Text Admin - Bootstrap
 *
 * Wires the toolbar, editor surface, and textarea syncing together.
 * This file is responsible for initialising editors on page load and
 * watching for dynamically added inline form rows.
 */
(function (root) {
    'use strict';

    // Bootstrap layer: wires editor DOM, toolbar, and events together.
    // Bootstrap is intentionally thin: it wires the helper modules to each textarea and keeps the DOM in sync.
    if (root.__richTextAdminBootstrapLoaded) {
        return;
    }

    root.__richTextAdminBootstrapLoaded = true;

    var api = root.RichTextAdminWidget || {};

    // Build a toolbar button with a command identifier.
    function createToolbarButton(label, title, commandName, onClick) {
        var button = document.createElement('button');

        button.type = 'button';
        button.textContent = label;
        button.title = title;
        button.dataset.command = commandName;
        button.setAttribute('aria-pressed', 'false');

        // Prevent the toolbar from stealing focus before the editor action runs.
        button.addEventListener('mousedown', function (event) {
            event.preventDefault();
        });
        button.addEventListener('click', onClick);

        return button;
    }

    // Update toolbar active states based on the current DOM selection.
    function updateToolbarState(toolbar, editor) {
        var activeBlock = api.getCurrentBlockElement(editor);
        var activeList = api.getCurrentListElement(editor);
        var isBoldActive = !!api.getCurrentInlineElement(editor, 'B');
        var isItalicActive = !!api.getCurrentInlineElement(editor, 'I');
        var isUnderlineActive = !!api.getCurrentInlineElement(editor, 'U');
        var isLinkActive = !!api.getCurrentInlineElement(editor, 'A');

        // Toolbar state is derived from the DOM tree so it works without deprecated browser commands.
        toolbar.querySelectorAll('button[data-command]').forEach(function (button) {
            var command = button.dataset.command;
            var isActive = false;

            if (command === 'bold') {
                isActive = isBoldActive;
            } else if (command === 'italic') {
                isActive = isItalicActive;
            } else if (command === 'underline') {
                isActive = isUnderlineActive;
            } else if (command === 'link') {
                isActive = isLinkActive;
            } else if (command === 'heading-h3') {
                isActive = !!activeBlock && activeBlock.tagName === 'H3';
            } else if (command === 'paragraph') {
                isActive = !!activeBlock && activeBlock.tagName === 'P';
            } else if (command === 'bullet-list') {
                isActive = !!activeList && activeList.tagName === 'UL';
            } else if (command === 'numbered-list') {
                isActive = !!activeList && activeList.tagName === 'OL';
            }

            button.classList.toggle('is-active', isActive);
            button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
        });
    }

    // Initialize a single textarea into a rich-text editor instance.
    function initTextarea(textarea) {
        var wrapper;
        var toolbar;
        var editor;
        var form;

        if (!textarea || textarea.dataset.richtextInitialized === '1') {
            return;
        }

        textarea.dataset.richtextInitialized = '1';
        api.ensureStyles();

        wrapper = document.createElement('div');
        wrapper.className = 'richtext-admin-wrapper';

        toolbar = document.createElement('div');
        toolbar.className = 'richtext-admin-toolbar';

        editor = document.createElement('div');
        editor.className = 'richtext-admin-editor';
        editor.contentEditable = 'true';

        // One hidden textarea maps to one live editor surface.
        // Execute a toolbar command and sync the textarea afterwards.
        function applyCommand(command) {
            if (command === 'bold') {
                api.toggleInlineTag(editor, 'B');
            } else if (command === 'italic') {
                api.toggleInlineTag(editor, 'I');
            } else if (command === 'underline') {
                api.toggleInlineTag(editor, 'U');
            } else if (command === 'heading-h3') {
                api.formatCurrentBlock(editor, 'H3');
            } else if (command === 'paragraph') {
                api.formatCurrentBlock(editor, 'P');
            } else if (command === 'bullet-list') {
                api.toggleList(editor, 'UL');
            } else if (command === 'numbered-list') {
                api.toggleList(editor, 'OL');
            } else if (command === 'link') {
                api.toggleLink(editor);
            } else if (command === 'clean') {
                api.clearFormatting(editor);
            }

            api.syncToTextarea(editor, textarea);
            window.setTimeout(function () {
                updateToolbarState(toolbar, editor);
            }, 0);
        }

        toolbar.appendChild(createToolbarButton('B', 'Bold', 'bold', function () {
            applyCommand('bold');
        }));
        toolbar.appendChild(createToolbarButton('I', 'Italic', 'italic', function () {
            applyCommand('italic');
        }));
        toolbar.appendChild(createToolbarButton('U', 'Underline', 'underline', function () {
            applyCommand('underline');
        }));
        toolbar.appendChild(createToolbarButton('H3', 'Heading', 'heading-h3', function () {
            applyCommand('heading-h3');
        }));
        toolbar.appendChild(createToolbarButton('P', 'Paragraph', 'paragraph', function () {
            applyCommand('paragraph');
        }));
        toolbar.appendChild(createToolbarButton('UL', 'Bullet list', 'bullet-list', function () {
            applyCommand('bullet-list');
        }));
        toolbar.appendChild(createToolbarButton('OL', 'Numbered list', 'numbered-list', function () {
            applyCommand('numbered-list');
        }));
        toolbar.appendChild(createToolbarButton('Link', 'Insert link', 'link', function () {
            applyCommand('link');
        }));
        toolbar.appendChild(createToolbarButton('Clean', 'Remove formatting', 'clean', function () {
            applyCommand('clean');
        }));

        editor.innerHTML = api.looksLikeHtml(textarea.value) || api.looksLikeEscapedHtml(textarea.value)
            ? api.buildPreviewHtml(textarea.value)
            : api.escapeHtml(textarea.value);

        // Normalize pasted HTML while letting plain text fall back to the browser.
        editor.addEventListener('paste', function (event) {
            var clipboard = event.clipboardData || window.clipboardData;
            var clipboardHtml;
            var clipboardText;
            var candidate;

            if (!clipboard) {
                return;
            }

            // Prefer HTML payloads; plain text is left to the browser if it is not markup.
            clipboardHtml = clipboard.getData('text/html');
            clipboardText = clipboard.getData('text/plain');
            candidate = clipboardHtml || clipboardText;

            if (!candidate || !api.looksLikeHtml(candidate)) {
                return;
            }

            event.preventDefault();
            candidate = api.buildPreviewHtml(candidate);

            if (api.insertHtmlAtCursor(candidate)) {
                api.syncToTextarea(editor, textarea);
                window.setTimeout(function () {
                    updateToolbarState(toolbar, editor);
                }, 0);
            }
        });

        // Keep textarea and toolbar state in sync on edits.
        editor.addEventListener('input', function () {
            api.syncToTextarea(editor, textarea);
            updateToolbarState(toolbar, editor);
        });

        // Sync on blur so admin saves the latest content.
        editor.addEventListener('blur', function () {
            api.syncToTextarea(editor, textarea);
        });

        // Keyboard-driven selection changes should refresh toolbar states.
        editor.addEventListener('keyup', function () {
            updateToolbarState(toolbar, editor);
        });

        // Mouse-driven selection changes should refresh toolbar states.
        editor.addEventListener('mouseup', function () {
            updateToolbarState(toolbar, editor);
        });

        // When focus enters the editor, ensure toolbar states are accurate.
        editor.addEventListener('focus', function () {
            updateToolbarState(toolbar, editor);
        });

        wrapper.appendChild(toolbar);
        wrapper.appendChild(editor);

        textarea.style.display = 'none';
        textarea.parentNode.insertBefore(wrapper, textarea);

        form = textarea.closest('form');
        if (form) {
            form.addEventListener('submit', function () {
                api.syncToTextarea(editor, textarea);
            });
        }

        updateToolbarState(toolbar, editor);
    }

    // Initialize all textareas inside the given scope.
    function initScope(scope) {
        var rootNode = scope || document;

        rootNode.querySelectorAll(api.SELECTOR).forEach(initTextarea);
    }

    // Listen for dynamically added inline form rows.
    function observeDom() {
        if (!document.body || typeof MutationObserver === 'undefined') {
            return;
        }

        // Inline form rows can appear after page load, so observe for newly inserted textareas.
        var observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                mutation.addedNodes.forEach(function (node) {
                    if (!node || node.nodeType !== 1) {
                        return;
                    }

                    if (node.matches && node.matches(api.SELECTOR)) {
                        initTextarea(node);
                        return;
                    }

                    if (node.querySelectorAll) {
                        initScope(node);
                    }
                });
            });
        });

        observer.observe(document.body, { childList: true, subtree: true });
    }

    // Boot once after DOM ready to hook existing and future inlines.
    function boot() {
        api.ensureStyles();
        initScope(document);
        observeDom();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})(window);
