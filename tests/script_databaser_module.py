import os

# Caminho raiz do seu projeto de código fonte
root_path = './Controle_Chaves'

# Importação antiga e nova (ajuste a nova se necessário)
old_import_line = 'from database_module import'
new_import_line = 'from database_module import'

def update_imports_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    changed = False
    with open(filepath, 'w', encoding='utf-8') as f:
        for line in lines:
            if line.strip().startswith(old_import_line):
                f.write(line.replace(old_import_line, new_import_line))
                changed = True
            else:
                f.write(line)
    return changed

def walk_and_update_imports():
    count = 0
    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            if filename.endswith('.py'):
                full_path = os.path.join(dirpath, filename)
                if update_imports_in_file(full_path):
                    print(f'Import updated in: {full_path}')
                    count += 1
    print(f'Total files updated: {count}')

if __name__ == "__main__":
    walk_and_update_imports()
