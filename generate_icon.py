from PIL import Image, ImageDraw

def create_clean_terminal_icon():
    sizes = [(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)]
    images = []

    for size in sizes:
        w, h = size
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 1. Скругленная карточка в стиле Windows 11 Fluent (все координаты — int)
        r = int(w // 4)
        pad = int(w * 0.05)
        border_width = max(1, int(w * 0.03))
        
        draw.rounded_rectangle(
            [pad, pad, int(w * 0.95), int(h * 0.95)],
            radius=r,
            fill=(30, 30, 32, 255),       # Плотный матовый темно-серый цвет
            outline=(60, 60, 65, 255),    # Тонкая контрастная рамка
            width=border_width
        )

        # 2. Четкий и узнаваемый символ терминала: знак «>» и мигающий блок курсора «_»
        if w >= 32:
            lw = max(3, int(w // 10))
            
            # Символ промпта '>'
            draw.line(
                [(int(w * 0.32), int(h * 0.35)), (int(w * 0.52), int(h * 0.5)), (int(w * 0.32), int(h * 0.65))],
                fill=(78, 201, 176, 255),  # Чистый бирюзовый акцент
                width=lw,
                joint="curve"
            )
            
            # Блок курсора ввода данных
            draw.rectangle(
                [int(w * 0.58), int(h * 0.52), int(w * 0.72), int(h * 0.65)],
                fill=(212, 212, 212, 255)  # Светлый активный курсор
            )

        images.append(img)

    icon_path = "icon.ico"
    images[0].save(
        icon_path,
        format="ICO",
        sizes=[(sz[0], sz[1]) for sz in sizes],
        append_images=images[1:]
    )
    print("Чистая иконка терминала создана!")

if __name__ == "__main__":
    create_clean_terminal_icon()