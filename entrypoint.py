import os
from pathlib import Path

try:
    import yaml
except ImportError:
    import subprocess
    
    subprocess.run(["pip", "install", "pyyaml"])
    import yaml
    
config_path = Path('config')

def load_config(name: str) -> dict:
    with open(config_path / f'{name}.yaml', 'r') as f:
        return yaml.safe_load(f)
    
def save_config(name: str, config: dict) -> None:
    with open(config_path / f'{name}.yaml', 'w') as f:
        yaml.safe_dump(config, f, encoding='utf-8', allow_unicode=True)
        
def set_database():
    config = load_config('database')
    if 'ENABLE_MYSQL' in os.environ and os.environ['ENABLE_MYSQL']:
        config['mode'] = 'mysql'
    else:
        return
    if 'MYSQL_HOST' in os.environ and os.environ['MYSQL_HOST']:
        config['config']['host'] = os.environ['MYSQL_HOST']
    if 'MYSQL_PORT' in os.environ and os.environ['MYSQL_PORT']:
        config['config']['port'] = int(os.environ['MYSQL_PORT'])
    if 'MYSQL_USER' in os.environ and os.environ['MYSQL_USER']:
        config['config']['user'] = os.environ['MYSQL_USER']
    if 'MYSQL_PASSWORD' in os.environ and os.environ['MYSQL_PASSWORD']:
        config['config']['password'] = os.environ['MYSQL_PASSWORD']
    save_config('database', config)
    
    
def set_prefix():
    config = load_config('prefix')
    if 'PREFIX' in os.environ and os.environ['PREFIX']:
        if os.environ['PREFIX'].startswith('[') and os.environ['PREFIX'].endswith(']'):
            prefixs = os.environ['PREFIX'][1:-1].split(',')
            new = []
            for prefix in prefixs:
                # remove space
                new.append(prefix.strip().replace('\'', '').replace('\"', '').replace('`', ''))
            prefixs = new
        else:
            prefixs = [os.environ['PREFIX']]
        config['prefix_keywords'] = prefixs
        save_config('prefix', config)
        
        
def set_server():
    config = load_config('server')
    config['host'] = '0.0.0.0'
    if 'AUTH' in os.environ and os.environ['AUTH']:
        config['authKey'] = os.environ['AUTH']
    save_config('server', config)
    
    
def main():
    set_database()
    set_prefix()
    set_server()
    
    
if __name__ == '__main__':
    main()
        
