import numpy as np
import matplotlib.pyplot as plt
import json
import pandas as pd
import seaborn as sns

# Графики плотности распределения скоров модели, а также эмпирической кумулятивной функции распределения

def plot_score_density_and_cdf(pred_scores, 
                               output_density='/app/output/pred_density.png', 
                               output_cdf='/app/output/pred_cdf.png'):
    """
    Строит график плотности (KDE) и ECDF для предсказанных скоров модели,
    сохраняет их в файлы.
    """
    plt.figure(figsize=(7, 4))
    sns.kdeplot(pred_scores, fill=True, color='#EA3338', alpha=0.6, linewidth=0.5, label='KDE-плотность')
    plt.xlabel('Предсказанная вероятность')
    plt.ylabel('Плотность')
    plt.title('Плотность предсказанных скоров (KDE)')
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.legend()
    plt.savefig(output_density)
    plt.close()

    # ECDF
    x = np.sort(pred_scores)
    y = np.arange(1, len(x) + 1) / len(x)
    plt.figure(figsize=(7, 4))
    plt.plot(x, y, color='#EA3338', linewidth=2, label='ECDF')
    plt.xlabel('Предсказанная вероятность')
    plt.ylabel('ECDF')
    plt.title('Эмпирическая CDF предсказанных скоров')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.legend()
    plt.savefig(output_cdf)
    plt.close()

# График важности признаков (стандартная по важности при построении дерева для построения быстрой оценки)

def plot_feature_importance(
    model, model_features, 
    output_path='output/top5_importance.png',
    json_path='output/top5_importances.json'
):
    """
    Сохраняет barplot топ-5 важнейших признаков CatBoost-модели и их значения в JSON.
    """
    importance_df = pd.DataFrame({
        'Признак': model_features,
        'Важность': model.get_feature_importance()
    }).sort_values('Важность', ascending=False)

    # Топ-5
    top_df = importance_df.head(5)[::-1]
    plt.figure(figsize=(8, 4))
    bars = plt.barh(
        top_df['Признак'],
        top_df['Важность'],
        color='#EA3338',
        edgecolor='black',
        linewidth=1.2
    )
    # Выделение синим: if len(bars) > 0: bars[-1].set_color('#ADD2FF')

    plt.title('Топ-5 признаков по важности', fontsize=14, fontweight='bold')
    plt.xlabel('Важность (Feature Importance)', fontsize=12)
    plt.ylabel('Признак', fontsize=12)
    plt.gca().invert_yaxis()
    plt.grid(True, linestyle='--', alpha=0.6, axis='x')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    
    # Сохранить топ-5 признаков и их значения в JSON
    top5_dict = dict(zip(top_df['Признак'], top_df['Важность']))
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(top5_dict, f, ensure_ascii=False, indent=2)