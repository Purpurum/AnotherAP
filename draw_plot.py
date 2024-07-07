import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
from PIL import Image

def generate_plots(df):
    # Преобразование столбцов с датами в тип datetime
    df['date_registration_start'] = pd.to_datetime(df['date_registration_start'])
    
    # Извлечение часа из времени начала регистрации
    df['hour'] = df['date_registration_start'].dt.hour
    
    # Словарь для перевода классов на русский
    class_translations = {
        'Bear': 'Медведь',
        'Cat': 'Кошка',
        'Wolverine': 'Росомаха',
        'Roe_Deer': 'Косуля',
        'Mountain_Goat': 'Горный козел',
        'Moose': 'Лось',
        'Musk_Deer': 'Кабарга',
        'Red_Deer': 'Благородный олень',
        'Racoon_Dog': 'Енотовидная собака',
        'Fox': 'Лиса',
        'Wolf': 'Волк',
        'Bison': 'Бизон',
        'Marten': 'Куница',
        'Badger': 'Барсук',
        'Hare': 'Заяц',
        'Snow_Leopard': 'Снежный барс',
        'Lynx': 'Рысь',
        'Squirrel': 'Белка',
        'Dog': 'Собака',
        'Goral': 'Горал',
        'Tiger': 'Тигр'
    }   
    # Уникальные номера ловушек
    trap_ids = df['folder_name'].unique()
    
    plots = {}

    fig, ax = plt.subplots(ncols = len(trap_ids))
    i = 0

    for trap_id in trap_ids:
        # Фильтрация данных для текущей ловушки
        trap_data = df[df['folder_name'] == trap_id]
        
        # График активности по часам суток
        hourly_class_counts = trap_data.groupby(['hour', 'class'])['count'].max().unstack(fill_value=0)
        hourly_class_counts.columns = [class_translations.get(col, col) for col in hourly_class_counts.columns]
        colors = sns.color_palette("Paired", len(hourly_class_counts.columns))
        hourly_class_counts.plot(kind='bar', 
                                 stacked=True,
                                 width=0.8, 
                                 color=colors,
                                   ax=ax[i])
        ax[i].set_title(f'Ловушка {trap_id}', fontsize=12)
        ax[i].set_xlabel('Час суток', fontsize=11)
        ax[i].set_ylabel('Количество регистраций', fontsize=11)
        ax[i].set_xticks(range(0, 24, 2))
        ax[i].set_xticklabels([f'{x}:00' for x in range(0, 24, 2)], rotation=45, fontsize=8)
        ax[i].legend(title='Вид животного', bbox_to_anchor=(0.6, 1), loc='upper left', fontsize=8)
    
        ax[i].grid(axis='y', linestyle='--', alpha=0.7)
        plots[f'hourly_activity_{trap_id}'] = fig
        
        i += 1

    fig.set_size_inches(20, 6)
    fig.tight_layout()

    img_bytes = io.BytesIO()
    fig.savefig('диаграмма.png', format='png')
    img_bytes.seek(0)
    
    # Загрузка изображения с помощью Pillow
    img = Image.open('диаграмма.png')
    
    return 'диаграмма.png' # Загрузка данных