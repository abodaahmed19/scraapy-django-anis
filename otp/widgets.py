# widgets.py
from django.forms import Textarea
from django.utils.safestring import mark_safe


class MarkdownWidget(Textarea):

    class Media:
        css = {
            'all': (
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
            )
        }
        js = (
            'https://cdn.jsdelivr.net/npm/marked/marked.min.js',
        )

    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'markdown-editor',
            'rows': 15,
            'cols': 40,
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        textarea_html = super().render(name, value, attrs, renderer)
        
        return mark_safe(
            self._get_css() + 
            '<div class="markdown-container">' +
            self._get_toolbar_row() + 
            self._get_editor_row(textarea_html) + 
            self._get_preview_row() + 
            '</div>' +
            self._get_scripts()
        )

    def _get_css(self):
        """Return the CSS styles for the widget"""
        return """
        <style>
            .markdown-container {
                display: flex;
                flex-direction: column;
                gap: 15px;
                width: 100%;
            }
            
            .markdown-row {
                width: 100%;
                border-radius: 6px;
                overflow: hidden;
            }
            
            .toolbar-row {
                background: #f8f9fa;
                padding: 10px;
                border: 1px solid #e1e4e8;
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }
            
            .editor-row {
                border: 1px solid #e1e4e8;
                border-radius: 6px;
                overflow: hidden;
            }
            
            .preview-row {
                border: 1px solid #e1e4e8;
                background: #f8f9fa;
                color: #000;
            }
            
            .markdown-toolbar button {
                background: white;
                border: 1px solid #d1d5da;
                padding: 8px 12px;
                cursor: pointer;
                border-radius: 4px;
                transition: all 0.2s ease;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                color: #24292e;
            }
            
            .markdown-toolbar button:hover {
                background: #f3f4f6;
                border-color: #959da5;
            }
            
            .markdown-toolbar button i {
                font-size: 14px;
                pointer-events: none;
            }
            
            .markdown-toolbar button small {
                font-size: 0.7em;
                margin-left: 3px;
            }
            
            .markdown-editor {
                width: 100%;
                min-height: 300px;
                font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
                font-size: 14px;
                padding: 12px;
                border: none;
                line-height: 1.5;
                resize: vertical;
                background: white;
                color: #24292e;
            }
            
            .markdown-editor:focus {
                outline: none;
                box-shadow: 0 0 0 2px rgba(3, 102, 214, 0.3);
            }
            
            .preview-header {
                padding: 12px 16px;
                background: #f6f8fa;
                border-bottom: 1px solid #e1e4e8;
                font-size: 14px;
                font-weight: 600;
                color: #24292e;
            }
            
            .markdown-preview-content {
                padding: 16px;
                min-height: 100px;
            }
            
            .markdown-preview-content p:last-child {
                margin-bottom: 0;
            }
            
            /* Dropdown menu */
            .dropdown {
                position: relative;
                display: inline-block;
                z-index: 2000;
            }
            
        .dropdown-menu {
            display: none !important;
            position: absolute;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            z-index: 99999;
            min-width: 120px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
           
            display: flex; 
            flex-direction: row; 
            gap: 4px; 
            padding: 4px; 
             transform: translate(40px, -40px);
        }

        .dropdown:hover .dropdown-menu {
            display: flex !important; 
        }

        .dropdown-menu button {

            width: auto; 
            text-align: center; 
            padding: 8px 12px;
            border: none;
            background: none;
            cursor: pointer;
            white-space: nowrap; 
        }
            
            .dropdown-menu button:hover {
                background: #f5f5f5;
            }
            

            .markdown-container:-webkit-full-screen {
                width: 100%;
                height: 100%;
                background: white;
                padding: 20px;
            }
            
            .markdown-container:-moz-full-screen {
                width: 100%;
                height: 100%;
                background: white;
                padding: 20px;
            }
            
            .markdown-container:-ms-fullscreen {
                width: 100%;
                height: 100%;
                background: white;
                padding: 20px;
            }
            
            .markdown-container:fullscreen {
                width: 100%;
                height: 100%;
                background: white;
                padding: 20px;
            }
            
            .toolbar-separator {
                border-left: 1px solid #d1d5da;
                margin: 0 5px;
            }
            
            
        </style>
        """

    def _get_toolbar_row(self):
        """Return the HTML for the toolbar row with all enhancements"""
        return """
        <div class="markdown-row toolbar-row">
            <div class="markdown-toolbar">
                <!-- Text Formatting -->
                <button type="button" title="Bold" onclick="formatText('**', '**')">
                    <i class="fas fa-bold"></i>
                </button>
                <button type="button" title="Italic" onclick="formatText('_', '_')">
                    <i class="fas fa-italic"></i>
                </button>
                <button type="button" title="Strikethrough" onclick="formatText('~~', '~~')">
                    <i class="fas fa-strikethrough"></i>
                </button>
                
                <!-- Headers -->
                <span class="toolbar-separator"></span>
                <button type="button" title="Heading 1" onclick="formatText('# ', '')">
                    <i class="fas fa-heading"></i><small>1</small>
                </button>
                <button type="button" title="Heading 2" onclick="formatText('## ', '')">
                    <i class="fas fa-heading"></i><small>2</small>
                </button>
                <button type="button" title="Heading 3" onclick="formatText('### ', '')">
                    <i class="fas fa-heading"></i><small>3</small>
                </button>
                
                <!-- Lists -->
                <span class="toolbar-separator"></span>
                <button type="button" title="Bullet List" onclick="formatText('* ', '')">
                    <i class="fas fa-list-ul"></i>
                </button>
                <button type="button" title="Numbered List" onclick="formatText('1. ', '')">
                    <i class="fas fa-list-ol"></i>
                </button>
                <button type="button" title="Checkbox" onclick="formatText('- [ ] ', '')">
                    <i class="far fa-square"></i>
                </button>
                
                <!-- Code -->
                <span class="toolbar-separator"></span>
                <button type="button" title="Code" onclick="formatText('`', '`')">
                    <i class="fas fa-code"></i>
                </button>
                <button type="button" title="Code Block" onclick="formatText('```\\n', '\\n```')">
                    <i class="fas fa-code"></i><small>block</small>
                </button>
                
                <!-- Links & Media -->
                <span class="toolbar-separator"></span>
                <button type="button" title="Link" onclick="formatText('[', '](url)')">
                    <i class="fas fa-link"></i>
                </button>
                <button type="button" title="Image" onclick="formatText('![', '](image-url)')">
                    <i class="fas fa-image"></i>
                </button>
                
                <!-- Block Elements -->
                <span class="toolbar-separator"></span>
                <button type="button" title="Blockquote" onclick="formatText('> ', '')">
                    <i class="fas fa-quote-right"></i>
                </button>
                <button type="button" title="Horizontal Rule" onclick="formatText('\\n---\\n', '')">
                    <i class="fas fa-minus"></i>
                </button>
                <button type="button" title="Table" onclick="insertTable()">
                    <i class="fas fa-table"></i>
                </button>
                
                <!-- Special Characters -->
                <span class="toolbar-separator"></span>
                <div class="dropdown">
                    <button type="button" title="Special Characters" class="dropdown-toggle">
                        <i class="fas fa-superscript"></i>
                    </button>
                    <div  class="dropdown-menu">
                        <button type="button" onclick="formatText('©', '')">© Copyright</button>
                        <button type="button" onclick="formatText('™', '')">™ Trademark</button>
                        <button type="button" onclick="formatText('°', '')">° Degree</button>
                        <button type="button" onclick="formatText('±', '')">± Plus-Minus</button>
                        <button type="button" onclick="formatText('×', '')">× Multiplication</button>
                    </div>
                </div>
                
                <!-- Text Direction -->
                
                <!-- Utilities -->
                <span class="toolbar-separator"></span>
                <button type="button" title="Insert Date" onclick="insertDateTime()">
                    <i class="far fa-calendar-alt"></i>
                </button>
                <button type="button" title="Clear Formatting" onclick="clearFormatting()">
                    <i class="fas fa-eraser"></i>
                </button>
                <button type="button" title="Toggle Fullscreen" onclick="toggleFullscreen()">
                    <i class="fas fa-expand"></i>
                </button>
                <button type="button" title="Markdown Help" onclick="window.open('https://www.markdownguide.org/cheat-sheet/')">
                    <i class="fas fa-question-circle"></i>
                </button>
            </div>
        </div>
        """

    def _get_editor_row(self, textarea_html):
        """Return the HTML for the editor row"""
        return f"""
        <div class="markdown-row editor-row">
            {textarea_html}
        </div>
        """

    def _get_preview_row(self):
        """Return the HTML for the preview row"""
        return """
        <div class="markdown-row preview-row">
            <div class="preview-header">Preview</div>
            <div class="markdown-preview-content" id="markdown-preview"></div>
        </div>
        """

    def _get_scripts(self):
        """Return the JavaScript for all widget functionality"""
        return """
        <script>
            // Unicode directional formatting characters
            const RLO = '\\u202E';  // Right-to-Left Override
            const LRO = '\\u202D';  // Left-to-Right Override
            const PDF = '\\u202C';  // Pop Directional Formatting

            function formatText(prefix, suffix) {
                const textarea = document.querySelector('textarea.markdown-editor');
                const start = textarea.selectionStart;
                const end = textarea.selectionEnd;
                const selectedText = textarea.value.substring(start, end);
                const newText = prefix + selectedText + suffix;
                
                textarea.value = 
                    textarea.value.substring(0, start) + 
                    newText + 
                    textarea.value.substring(end);
                
                textarea.focus();
                textarea.setSelectionRange(
                    start + prefix.length, 
                    start + prefix.length + selectedText.length
                );
                updatePreview();
            }

            function setDirection(direction) {
                const textarea = document.querySelector('textarea.markdown-editor');
                const start = textarea.selectionStart;
                const end = textarea.selectionEnd;
                const selectedText = textarea.value.substring(start, end);
                
                let newText;
                if (direction === 'rtl') {
                    newText = RLO + selectedText + PDF;
                } else { // ltr
                    newText = LRO + selectedText + PDF;
                }
                
                textarea.value = 
                    textarea.value.substring(0, start) + 
                    newText + 
                    textarea.value.substring(end);
                
                textarea.focus();
                const newCursorPos = direction === 'rtl' 
                    ? start + newText.length 
                    : start + 1;
                textarea.setSelectionRange(newCursorPos, newCursorPos);
                updatePreview();
            }

            // Insert table template
            function insertTable() {
                const tableTemplate = 
            `| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |`;
                
                formatText('\\n' + tableTemplate + '\\n\\n', '');
            }

            // Insert current date/time
            function insertDateTime() {
                const now = new Date();
                formatText(now.toLocaleString(), '');
            }

            // Toggle fullscreen
            function toggleFullscreen() {
                const container = document.querySelector('.markdown-container');
                if (!document.fullscreenElement) {
                    container.requestFullscreen().catch(err => {
                        console.error('Fullscreen error:', err);
                    });
                } else {
                    document.exitFullscreen();
                }
            }

            // Clear formatting from selected text
            function clearFormatting() {
                const textarea = document.querySelector('textarea.markdown-editor');
                const start = textarea.selectionStart;
                const end = textarea.selectionEnd;
                const selectedText = textarea.value.substring(start, end);
                
                // Remove markdown formatting
                const cleanText = selectedText
                    .replace(/(\*\*|__)(.*?)\1/g, '$2')  // bold
                    .replace(/(\*|_)(.*?)\1/g, '$2')     // italic
                    .replace(/~~(.*?)~~/g, '$1')         // strikethrough
                    .replace(/`(.*?)`/g, '$1')           // inline code
                    .replace(/^#+\s+/gm, '')             // headers
                    .replace(/^\s*[-*+]\s+/gm, '')       // list items
                    .replace(/^>\s+/gm, '');             // blockquotes
                
                textarea.value = 
                    textarea.value.substring(0, start) + 
                    cleanText + 
                    textarea.value.substring(end);
                
                textarea.focus();
                textarea.setSelectionRange(start, start + cleanText.length);
                updatePreview();
            }

            function updatePreview() {
                const textarea = document.querySelector('textarea.markdown-editor');
                const preview = document.getElementById('markdown-preview');
                
                if (textarea && preview) {
                    try {
                        preview.innerHTML = marked.parse(textarea.value);
                    } catch (e) {
                        preview.innerHTML = '<p class="text-error">Error rendering preview</p>';
                        console.error('Markdown preview error:', e);
                    }
                }
            }

            document.addEventListener('DOMContentLoaded', function() {
                const textarea = document.querySelector('textarea.markdown-editor');
                if (textarea) {
                    textarea.addEventListener('input', updatePreview);
                    textarea.addEventListener('change', updatePreview);
                    updatePreview();  // Initialize preview
                }
            });
        </script>
        """