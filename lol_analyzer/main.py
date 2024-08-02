import requests
from bs4 import BeautifulSoup
import re
import os
import pickle


class Champion:
    def __init__(self, name, role, tier):
        self.name = name
        self.id = re.sub(r'[^a-zA-Z0-9]', '', name.lower())
        self.role = role

        res = requests.get(
            f'https://www.op.gg/champions/{self.id}/counters/{self.role}?tier={tier}')
        soup = BeautifulSoup(res.text, 'html.parser')

        # Get winrate against other champions
        self.counters = {}
        for c in soup.select('aside')[0].select('tbody')[0].select('tr'):
            champion_name = re.sub(
                r'[^a-zA-Z0-9]', '', c.select('td')[1].text.lower())
            winrate = float(re.sub(r'[^0-9.]', '', c.select('td')[2].text))
            self.counters[champion_name] = winrate

    def __str__(self):
        return f'{self.name} ({self.role})'

    def get_winrate_against(self, champion_name):
        champion_name = re.sub(r'[^a-zA-Z0-9]', '', champion_name.lower())
        if champion_name not in self.counters:
            return None
        return self.counters[champion_name]


def data_collect(config):
    position = config['position']
    tier = config['tier']

    res = requests.get(
        f'https://www.op.gg/champions?position={position}&tier={tier}')
    soup = BeautifulSoup(res.text, 'html.parser')
    champions = soup.select('main')[0].select('tbody')[0].select('tr')
    champion_names = [champ.select('td')[1].text for champ in champions]

    champions = []
    for name in champion_names:
        champions.append(Champion(name, position, tier))
    os.makedirs('data', exist_ok=True)

    with open(f'data/{position}_{tier}.pkl', 'wb') as f:
        pickle.dump(champions, f)


def main(config):
    position = 'mid'
    tier = 'bronze'
    champion_pool_names = config['champion_pool']

    champions = None
    with open(f'data/{position}_{tier}.pkl', 'rb') as f:
        champions = pickle.load(f)

    champion_pool = []
    for name in champion_pool_names:
        for champ in champions:
            if champ.name == name:
                champion_pool.append(champ)
                break

    for enemy_champ in champions:
        max_winrate = 0
        max_winrate_champion = None
        for my_champ in champion_pool:
            winrate = my_champ.get_winrate_against(enemy_champ.name)
            if winrate is None:
                continue
            if winrate > max_winrate:
                max_winrate = winrate
                max_winrate_champion = my_champ

        if max_winrate_champion is None:
            print(f'{enemy_champ.name} -> No champion found')
        else:
            if max_winrate > 52:
                print(
                    f'{enemy_champ.name} -> {max_winrate_champion.name} (\033[32m{max_winrate}%\033[0m)')
            elif max_winrate < 48:
                print(
                    f'{enemy_champ.name} -> {max_winrate_champion.name} (\033[31m{max_winrate}%\033[0m)')
            else:
                print(
                    f'{enemy_champ.name} -> {max_winrate_champion.name} ({max_winrate}%)')


if __name__ == '__main__':
    import yaml
    with open('config.yaml', 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_collect', action='store_true')

    args = parser.parse_args()
    if (args.data_collect):
        data_collect(config)
    else:
        main(config)
