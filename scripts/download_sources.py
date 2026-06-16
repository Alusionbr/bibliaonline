
import os
import requests
import zipfile
import io

def download_file(url, path):
    print(f"Baixando {url} para {path}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Download de {url} concluído.")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar {url}: {e}")
        return False
    return True

def download_and_unzip(url, extract_to_dir):
    print(f"Baixando e descompactando {url} para {extract_to_dir}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(response.content))
        z.extractall(extract_to_dir)
        print(f"Download e descompactação de {url} concluídos.")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar {url}: {e}")
        return False
    except zipfile.BadZipFile as e:
        print(f"Erro ao descompactar {url}: {e}")
        return False
    return True

def main():
    # URLs e caminhos de destino
    sources = [
        {
            'url': 'http://www.gutenberg.org/files/62383/62383-0.txt',
            'path': 'v4/raw_materials/biblia/almeida_gutenberg_62383.txt',
            'type': 'file'
        },
        {
            'url': 'https://www.gutenberg.org/cache/epub/8294/pg8294-h.zip',
            'path': 'v4/raw_materials/biblia/world_english_bible_html.zip',
            'type': 'zip'
        },
        {
            'url': 'https://github.com/openscriptures/morphhb/archive/master.zip',
            'path': 'v4/raw_materials/originais/openscripts_morphhb_master.zip',
            'type': 'zip'
        }
    ]

    for source in sources:
        os.makedirs(os.path.dirname(source['path']), exist_ok=True)
        if source['type'] == 'file':
            download_file(source['url'], source['path'])
        elif source['type'] == 'zip':
            # Para arquivos zip, baixamos e salvamos o zip, não descompactamos automaticamente aqui.
            # O usuário pediu para criar o arquivo .zip, não para extraí-lo.
            download_file(source['url'], source['path'])

if __name__ == '__main__':
    main()
