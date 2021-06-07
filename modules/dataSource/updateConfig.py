import json


class Config:
    with open('resource/config/update_config.json', encoding='utf-8', mode='r')as file:
        update_config = json.load(file)

    high_star = update_config['high_star']
    classes = update_config['classes']
    types = update_config['types']
    limit = update_config['limit'] + update_config['linkage']
    unavailable = [item for item in
                   update_config['unavailable']['not_normally'] +
                   update_config['unavailable']['sale_only'] +
                   update_config['unavailable']['recruit_only'] +
                   update_config['unavailable']['activity_only'] +
                   update_config['unavailable']['contract_only'] +
                   update_config['unavailable']['roguelike_only'] +
                   update_config['unavailable']['linkage_only']]
