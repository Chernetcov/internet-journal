(function () {
    'use strict';

    const PICTURE_ICON = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 122.88 91.27"><path fill="currentColor" fill-rule="evenodd" d="M87.29,16.88A11.35,11.35,0,1,1,75.94,28.23,11.35,11.35,0,0,1,87.29,16.88Zm27.33,74.39H8.26a8.27,8.27,0,0,1-5.83-2.44h0A8.24,8.24,0,0,1,0,83V8.26A8.26,8.26,0,0,1,2.42,2.42h0A8.26,8.26,0,0,1,8.26,0H114.62a8.26,8.26,0,0,1,5.83,2.43h0a8.26,8.26,0,0,1,2.42,5.84V83a8.24,8.24,0,0,1-2.42,5.83h0a8.27,8.27,0,0,1-5.83,2.44Zm-7.35-9.43L87.6,50.46a4.52,4.52,0,0,0-7.65,0L70.66,65.39,80.77,81.84H76.62l-27.57-44c-2.54-3.39-6.61-3.13-8.88,0l-27,44H9.42V9.42h104V81.84Z"/></svg>';

    function libraryUrl() {
        return window.CKEDITOR_IMAGE_LIBRARY_URL || '/images/';
    }

    function createElement(tagName, className, text) {
        const element = document.createElement(tagName);
        if (className) {
            element.className = className;
        }
        if (text) {
            element.textContent = text;
        }
        return element;
    }

    /**
     * Собственный плагин CKEditor 5: кнопка «Библиотека изображений».
     *
     * Плагин регистрирует элемент панели `imageLibrary`, открывает модальное
     * окно со списком изображений из ImageStore и вставляет выбранное
     * изображение в содержимое статьи.
     */
    class ImageLibraryPlugin {
        static get pluginName() {
            return 'ImageLibrary';
        }

        constructor(editor) {
            this.editor = editor;
            this._modal = null;
            this._previousFocus = null;
        }

        init() {
            const editor = this.editor;

            editor.ui.componentFactory.add('imageLibrary', locale => this._createButton(locale));
        }

        destroy() {
            this._close();
        }

        _createButton(locale) {
            // Классы представлений CKEditor не экспортируются глобально из сборки
            // django-ckeditor-5. Получаем базовый ButtonView через уже
            // зарегистрированный компонент панели.
            const sample = this.editor.ui.componentFactory.create('bold');
            const ButtonView = sample.constructor;
            if (typeof sample.destroy === 'function') {
                sample.destroy();
            }

            const button = new ButtonView(locale);
            button.set({
                label: 'Библиотека изображений',
                tooltip: true,
                icon: PICTURE_ICON,
            });
            button.on('execute', () => this._open());

            return button;
        }

        _open() {
            if (this._modal) {
                return;
            }

            this._previousFocus = document.activeElement;

            const overlay = createElement('div', 'iju-image-library');
            overlay.addEventListener('mousedown', event => {
                if (event.target === overlay) {
                    this._close();
                }
            });

            const dialog = createElement('div', 'iju-image-library__dialog');
            dialog.setAttribute('role', 'dialog');
            dialog.setAttribute('aria-modal', 'true');
            dialog.setAttribute('aria-labelledby', 'iju-image-library-title');

            const header = createElement('div', 'iju-image-library__header');
            const title = createElement('h2', 'iju-image-library__title', 'Библиотека изображений');
            title.id = 'iju-image-library-title';
            header.appendChild(title);

            const closeButton = createElement('button', 'iju-image-library__close', 'Закрыть');
            closeButton.type = 'button';
            closeButton.addEventListener('click', () => this._close());
            header.appendChild(closeButton);

            const body = createElement('div', 'iju-image-library__body');
            const status = createElement('p', 'iju-image-library__status', 'Загрузка изображений…');
            const grid = createElement('div', 'iju-image-library__grid');
            body.appendChild(status);
            body.appendChild(grid);

            dialog.appendChild(header);
            dialog.appendChild(body);
            overlay.appendChild(dialog);
            document.body.appendChild(overlay);

            this._modal = overlay;
            this._status = status;
            this._grid = grid;

            this._onKeyDown = event => {
                if (event.key === 'Escape') {
                    this._close();
                }
            };
            document.addEventListener('keydown', this._onKeyDown);

            closeButton.focus();
            this._loadImages();
        }

        _close() {
            if (!this._modal) {
                return;
            }

            this._modal.remove();
            this._modal = null;
            this._status = null;
            this._grid = null;

            if (this._onKeyDown) {
                document.removeEventListener('keydown', this._onKeyDown);
                this._onKeyDown = null;
            }

            if (this._previousFocus && typeof this._previousFocus.focus === 'function') {
                this._previousFocus.focus();
            }
            this._previousFocus = null;

            if (this.editor && this.editor.editing) {
                this.editor.editing.view.focus();
            }
        }

        async _loadImages() {
            try {
                const url = new URL(libraryUrl(), window.location.origin);
                url.searchParams.set('page_size', '100');

                const response = await fetch(url.toString(), {
                    headers: {Accept: 'application/json'},
                    credentials: 'same-origin',
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();
                const images = Array.isArray(data.results) ? data.results : [];

                if (!images.length) {
                    this._status.textContent = 'В библиотеке пока нет изображений.';
                    return;
                }

                this._status.hidden = true;
                images.forEach(image => this._grid.appendChild(this._createImageCard(image)));
            } catch (error) {
                console.error('Не удалось загрузить библиотеку изображений.', error);
                this._status.textContent = 'Не удалось загрузить изображения. Попробуйте ещё раз.';
            }
        }

        _createImageCard(image) {
            const card = createElement('button', 'iju-image-library__card');
            card.type = 'button';
            card.title = 'Вставить изображение';

            const preview = createElement('img', 'iju-image-library__image');
            preview.src = image.url;
            preview.alt = image.caption || '';
            preview.loading = 'lazy';
            if (image.srcset) {
                preview.srcset = image.srcset;
            }
            card.appendChild(preview);

            if (image.caption) {
                card.appendChild(
                    createElement('span', 'iju-image-library__caption', image.caption)
                );
            }

            card.addEventListener('click', () => this._insertImage(image));
            return card;
        }

        _insertImage(image) {
            const command = this.editor.commands.get('insertImage');
            if (!command || !command.isEnabled) {
                this._status.hidden = false;
                this._status.textContent = 'Изображение нельзя вставить в текущую позицию.';
                return;
            }

            const source = {
                src: image.url,
                alt: image.caption || '',
            };
            if (image.srcset) {
                source.srcset = image.srcset;
            }

            this.editor.execute('insertImage', {source});
            this._close();
        }
    }

    /**
     * django-ckeditor-5 создаёт редакторы из глобального `ClassicEditor`.
     * Добавляем плагин в список плагинов каждого создаваемого редактора.
     */
    function installImageLibraryPlugin() {
        const ClassicEditor = window.ClassicEditor;
        if (!ClassicEditor || ClassicEditor.__ijuImageLibraryInstalled) {
            return Boolean(ClassicEditor);
        }

        const originalCreate = ClassicEditor.create;
        ClassicEditor.create = function (sourceElementOrData, config) {
            const editorConfig = config || {};
            const plugins = Array.isArray(editorConfig.plugins)
                ? editorConfig.plugins.slice()
                : Array.from(ClassicEditor.builtinPlugins || []);

            if (!plugins.includes(ImageLibraryPlugin)) {
                plugins.push(ImageLibraryPlugin);
            }
            editorConfig.plugins = plugins;

            return originalCreate.call(this, sourceElementOrData, editorConfig);
        };
        ClassicEditor.__ijuImageLibraryInstalled = true;

        return true;
    }

    if (!installImageLibraryPlugin()) {
        document.addEventListener('DOMContentLoaded', installImageLibraryPlugin);
    }
})();
