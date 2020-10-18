from ScrapingUtils import get_fan_data
import time


nicknames = ['颜宇阿_',
             'Alina丶颜宇宏',
             '完颜宇龙',
             '颜宇--',
             '陌曦颜宇',
             '颜宇迪要多喝白开水',
             '是你们的翩雪a',
             '顺势交易',
             '趋势交易顺势而为',
             '顺势交易_',
             '顺势交易财神v炒股票为生',
             '芒果影娱',
             '向上娱乐',
             '亮程学长',
             'SUZOO点点',
             '买个熊猫炖土豆',
             '吃一堑长一智201904',
             '巧克力味左卫门',
             '陈尚辉',
             '收手吧陈尚辉',
             '陈尚辉a']

# driver = create_webdriver(headless=False)
# driver.get('https://weibo.com/cn')

# print(get_fan_data(nicknames[-1]))

for _ in range(100):
    for i in range(len(nicknames)):
        fan_cnt = get_fan_data(nicknames[i])
        print(f'{nicknames[i]}: {fan_cnt}')
