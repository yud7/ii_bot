import configparser
import aiogram


config = configparser.ConfigParser()
configPath = "config.ini"
config.read(configPath)

botToken = config.get('default', 'botToken')

if __name__ == '__main__':
    print()
