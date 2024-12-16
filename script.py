import os
import subprocess
import sys
import tempfile
from graphviz import Digraph
from datetime import datetime

def get_commit_graph(repo_path, file_hash):
    """Получить граф коммитов для заданного хеша файла."""
    os.chdir(repo_path)
    commits = subprocess.check_output([
        "git", "log", "--pretty=format:%H %ct", "--", file_hash
    ]).decode("utf-8").splitlines()

    graph = {}
    commit_data = []

    for i, commit_line in enumerate(commits, 1):
        commit_hash, commit_time = commit_line.split()
        parent_commits = subprocess.check_output([
            "git", "log", "--pretty=%P", "-n", "1", commit_hash
        ]).decode("utf-8").split()

        graph[commit_hash] = parent_commits

        # Преобразование времени в читаемый формат
        readable_time = datetime.utcfromtimestamp(int(commit_time)).strftime('%d %b %Y %H:%M:%S')
        commit_data.append((i, commit_hash, readable_time))

    return graph, commit_data

def generate_graphviz(graph, commit_data):
    """Создать представление графа в формате Graphviz."""
    dot = Digraph()

    for i, commit, commit_time in commit_data:
        formatted_label = f"{i}. {commit}\n{commit_time}"
        dot.node(commit, formatted_label)

    for commit, parents in graph.items():
        for parent in parents:
            dot.edge(parent, commit)

    return dot

def visualize_graph(graphviz_tool_path, graph):
    """Визуализировать граф с использованием Graphviz."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".gv") as temp_file:
        temp_file.write(graph.source.encode("utf-8"))
        temp_file.close()

        output_image = temp_file.name.replace(".gv", ".png")
        subprocess.run([graphviz_tool_path, "-Tpng", temp_file.name, "-o", output_image])
        print(f"Граф сохранен как {output_image}")

        # Открыть файл изображения, если это возможно
        if os.name == "nt":
            os.startfile(output_image)
        elif sys.platform == "darwin":
            subprocess.run(["open", output_image])
        else:
            subprocess.run(["xdg-open", output_image])

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Визуализация графа зависимостей git.")
    parser.add_argument("graphviz_tool_path", help="Путь к инструменту Graphviz dot.")
    parser.add_argument("repo_path", help="Путь к git-репозиторию.")
    parser.add_argument("file_hash", help="Хеш файла для анализа.")

    args = parser.parse_args()

    if not os.path.exists(args.graphviz_tool_path):
        print("Ошибка: инструмент Graphviz не найден по указанному пути.")
        sys.exit(1)

    if not os.path.exists(args.repo_path):
        print("Ошибка: путь к репозиторию не существует.")
        sys.exit(1)

    try:
        graph, commit_data = get_commit_graph(args.repo_path, args.file_hash)
        dot_graph = generate_graphviz(graph, commit_data)
        visualize_graph(args.graphviz_tool_path, dot_graph)
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)
