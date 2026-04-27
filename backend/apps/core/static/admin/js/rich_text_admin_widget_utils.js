/*
 * Rich Text Admin - Utilities
 *
 * Provides shared DOM helpers, selection utilities, and safe preview rendering.
 * The bootstrap and actions layers call into this module; this file avoids any
 * editor wiring or event listeners on purpose.
 */
(function (root) {
    'use strict';

    // Utility layer: DOM helpers, selection utilities, and safe preview rendering.
    // Shared helpers live in one namespace so the bootstrap file stays small and readable.
    var api = root.RichTextAdminWidget || (root.RichTextAdminWidget = {});

    // Stable IDs and selectors used across modules.
    api.STYLE_ID = 'richtext-admin-widget-style';
    api.SELECTOR = 'textarea[data-richtext-editor="1"]';

    // Inject the editor styles once per page.
    api.ensureStyles = function ensureStyles() {
        // Inject the editor CSS once so dynamically added inlines reuse the same styling.
        if (document.getElementById(api.STYLE_ID)) {
            return;
        }

        var style = document.createElement('style');
        style.id = api.STYLE_ID;
        style.textContent = [
            '.richtext-admin-wrapper { border: 1px solid #d0d7de; border-radius: 6px; background: #fff; width: 100%; max-width: 920px; box-sizing: border-box; }',
            '.richtext-admin-toolbar { display: flex; flex-wrap: wrap; gap: 4px; padding: 6px; border-bottom: 1px solid #e5e7eb; background: #f8fafc; }',
            '.richtext-admin-toolbar button { border: 1px solid #d1d5db; background: #fff; border-radius: 4px; padding: 3px 8px; cursor: pointer; font-size: 12px; }',
            '.richtext-admin-toolbar button:hover { background: #f3f4f6; }',
            '.richtext-admin-toolbar button.is-active { background: #dbeafe; border-color: #60a5fa; color: #1e3a8a; }',
            '.richtext-admin-editor { min-height: 180px; max-height: 460px; overflow: auto; padding: 10px; line-height: 1.5; width: 100%; box-sizing: border-box; }',
            '.richtext-admin-editor ul { display: block !important; list-style: none !important; margin: 0.5em 0 0.5em 0 !important; padding-left: 0 !important; }',
            '.richtext-admin-editor ol { display: block !important; list-style: none !important; margin: 0.5em 0 0.5em 0 !important; padding-left: 0 !important; counter-reset: richtext-list-item !important; }',
            '.richtext-admin-editor li { display: block !important; position: relative !important; margin: 0.2em 0 !important; padding-left: 1.5em !important; }',
            '.richtext-admin-editor ul > li::before { content: "•"; position: absolute; left: 0.2em; top: 0; }',
            '.richtext-admin-editor ol > li { counter-increment: richtext-list-item !important; }',
            '.richtext-admin-editor ol > li::before { content: counter(richtext-list-item) "."; position: absolute; left: 0; top: 0; }',
            '.richtext-admin-editor:focus { outline: 2px solid #79aec8; outline-offset: -2px; }',
            '.richtext-admin-input { width: 100%; box-sizing: border-box; }'
        ].join('');
        document.head.appendChild(style);
    };

    // Decode stored HTML entities before rendering content into the editor preview.
    api.decodeHtmlEntities = function decodeHtmlEntities(value) {
        // Turn stored escaped HTML back into something the DOM can preview safely.
        var decoder = document.createElement('textarea');
        decoder.innerHTML = value || '';
        return decoder.value;
    };

    // Quick HTML detection for paste/preview decisions.
    api.looksLikeHtml = function looksLikeHtml(value) {
        return /<\/?[a-z][\s\S]*>/i.test(value || '');
    };

    // Detect escaped tags so we can decode and preview them.
    api.looksLikeEscapedHtml = function looksLikeEscapedHtml(value) {
        return /&lt;|&gt;|&#\d+;|&amp;/i.test(value || '');
    };

    // Escape content when rendering plain text into the editor.
    api.escapeHtml = function escapeHtml(value) {
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    };

    // Allowlist for the lightweight preview renderer.
    api.isAllowedTag = function isAllowedTag(tagName) {
        return ['A', 'B', 'BLOCKQUOTE', 'BR', 'EM', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'I', 'LI', 'OL', 'P', 'SPAN', 'STRONG', 'U', 'UL'].indexOf(tagName) !== -1;
    };

    // Serialize preview markup with an allowlist to avoid executing arbitrary HTML.
    api.serializePreviewNode = function serializePreviewNode(node) {
        var children;
        var tagName;

        if (!node) {
            return '';
        }

        if (node.nodeType === Node.TEXT_NODE) {
            return api.escapeHtml(node.nodeValue);
        }

        if (node.nodeType !== Node.ELEMENT_NODE) {
            return '';
        }

        // Keep only a small HTML whitelist so the admin preview stays predictable.
        tagName = node.tagName;
        if (!api.isAllowedTag(tagName)) {
            return api.escapeHtml(node.outerHTML || node.textContent || '');
        }

        if (tagName === 'BR') {
            return '<br>';
        }

        children = Array.prototype.map.call(node.childNodes, api.serializePreviewNode).join('');

        if (tagName === 'A') {
            var href = node.getAttribute('href') || '';
            return '<a href="' + api.escapeHtml(href) + '">' + children + '</a>';
        }

        return '<' + tagName.toLowerCase() + '>' + children + '</' + tagName.toLowerCase() + '>';
    };

    // Build sanitized preview HTML for existing stored content.
    api.buildPreviewHtml = function buildPreviewHtml(value) {
        var decoded = api.decodeHtmlEntities(value || '');
        var container;

        if (!decoded) {
            return '';
        }

        container = document.createElement('div');
        container.innerHTML = decoded;

        return Array.prototype.map.call(container.childNodes, api.serializePreviewNode).join('');
    };

    // Get a selection range scoped to the editor, or null when the selection is outside.
    api.getSelectionRange = function getSelectionRange(editor) {
        var selection = window.getSelection ? window.getSelection() : null;

        if (!selection || selection.rangeCount === 0) {
            return null;
        }

        if (!editor.contains(selection.anchorNode) || !editor.contains(selection.focusNode)) {
            return null;
        }

        return selection.getRangeAt(0);
    };

    // Walk up the DOM tree until the matcher matches or we hit the editor root.
    api.findAncestorElement = function findAncestorElement(node, matcher, stopNode) {
        var current = node;

        if (!current) {
            return null;
        }

        if (current.nodeType === Node.TEXT_NODE) {
            current = current.parentElement;
        }

        while (current && current !== stopNode) {
            if (matcher(current)) {
                return current;
            }
            current = current.parentElement;
        }

        return null;
    };

    // Basic block-level tags we care about for toolbar state and formatting.
    api.isBlockTag = function isBlockTag(tagName) {
        return /^H[1-6]$/.test(tagName) || tagName === 'P' || tagName === 'BLOCKQUOTE' || tagName === 'LI';
    };

    // Determine which block element the caret currently sits in.
    api.getCurrentBlockElement = function getCurrentBlockElement(editor) {
        var selection = window.getSelection ? window.getSelection() : null;

        if (!selection || selection.rangeCount === 0) {
            return null;
        }

        return api.findAncestorElement(selection.anchorNode, function (element) {
            return element.tagName && api.isBlockTag(element.tagName);
        }, editor);
    };

    // Find the nearest UL/OL ancestor for list state tracking.
    api.getCurrentListElement = function getCurrentListElement(editor) {
        var selection = window.getSelection ? window.getSelection() : null;

        if (!selection || selection.rangeCount === 0) {
            return null;
        }

        return api.findAncestorElement(selection.anchorNode, function (element) {
            return element.tagName === 'UL' || element.tagName === 'OL';
        }, editor);
    };

    // Find the nearest inline tag for bold/italic/underline/link state tracking.
    api.getCurrentInlineElement = function getCurrentInlineElement(editor, tagName) {
        var selection = window.getSelection ? window.getSelection() : null;

        if (!selection || selection.rangeCount === 0) {
            return null;
        }

        return api.findAncestorElement(selection.anchorNode, function (element) {
            return element.tagName === tagName;
        }, editor);
    };

    // Copy attributes when swapping tag names to preserve data/links.
    api.copyAttributes = function copyAttributes(source, target) {
        Array.prototype.forEach.call(source.attributes, function (attribute) {
            target.setAttribute(attribute.name, attribute.value);
        });
    };

    // Replace a tag with another while preserving inner HTML and attributes.
    api.replaceElementTagName = function replaceElementTagName(element, tagName) {
        var replacement = document.createElement(tagName);

        api.copyAttributes(element, replacement);
        replacement.innerHTML = element.innerHTML;
        element.parentNode.replaceChild(replacement, element);

        return replacement;
    };

    // Remove a wrapper element while keeping its children in place.
    api.unwrapElement = function unwrapElement(element) {
        var parent = element.parentNode;

        while (element.firstChild) {
            parent.insertBefore(element.firstChild, element);
        }

        parent.removeChild(element);
    };

    // Place the caret inside an element after formatting changes.
    api.setCaretInsideElement = function setCaretInsideElement(element) {
        var selection = window.getSelection ? window.getSelection() : null;
        var range;

        if (!selection) {
            return;
        }

        range = document.createRange();
        if (element.lastChild && element.lastChild.nodeType === Node.TEXT_NODE) {
            range.setStart(element.lastChild, element.lastChild.nodeValue.length);
        } else {
            range.selectNodeContents(element);
            range.collapse(false);
        }

        selection.removeAllRanges();
        selection.addRange(range);
    };

    // Select all contents of a node so follow-up actions can wrap/replace it.
    api.selectNodeContents = function selectNodeContents(node) {
        var selection = window.getSelection ? window.getSelection() : null;
        var range;

        if (!selection) {
            return;
        }

        range = document.createRange();
        range.selectNodeContents(node);
        selection.removeAllRanges();
        selection.addRange(range);
    };

    // Wrap a selection range with a new element, handling collapsed ranges.
    api.wrapRangeWithElement = function wrapRangeWithElement(range, element) {
        var content;

        if (range.collapsed) {
            // Insert a zero-width space so the caret can live inside an empty wrapper.
            element.appendChild(document.createTextNode('\u200B'));
            range.insertNode(element);
            api.setCaretInsideElement(element);
            return element;
        }

        content = range.extractContents();
        element.appendChild(content);
        range.insertNode(element);
        api.selectNodeContents(element);

        return element;
    };

    // Insert HTML at the caret while preserving the selection.
    api.insertHtmlAtCursor = function insertHtmlAtCursor(html) {
        var selection = window.getSelection ? window.getSelection() : null;
        var range;
        var container;
        var fragment;
        var node;
        var lastNode = null;

        if (!selection || selection.rangeCount === 0) {
            return false;
        }

        range = selection.getRangeAt(0);
        range.deleteContents();

        container = document.createElement('div');
        container.innerHTML = html;

        fragment = document.createDocumentFragment();
        while ((node = container.firstChild)) {
            lastNode = fragment.appendChild(node);
        }

        range.insertNode(fragment);

        if (lastNode) {
            range = range.cloneRange();
            range.setStartAfter(lastNode);
            range.collapse(true);
            selection.removeAllRanges();
            selection.addRange(range);
        }

        return true;
    };

    // Keep the hidden textarea in sync so Django saves the HTML.
    api.syncToTextarea = function syncToTextarea(editor, textarea) {
        textarea.value = editor.innerHTML;
    };
})(window);
