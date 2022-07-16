import networkx as nx
import matplotlib.pyplot as plt
import random

from sys import argv
from hashlib import sha256
from random import getrandbits

from pathlib import Path

DEFAULT_OUTPUT_PATH = 'generated/graphs'
DEFAULT_OUTPUT_FILE_NAME = 'graph.png'



def color_graph(color_map):
    colors_names = ["blue", "yellow", "red"]
    random.shuffle(colors_names)
    color_list = [colors_names[index-1] for index in color_map]

    return color_list
    
def save_graph(graph, node_color=None, output_path=f'{DEFAULT_OUTPUT_PATH}/{DEFAULT_OUTPUT_FILE_NAME}'):
    # plt.figure changes the current active figure to a new one 
    plt.figure(output_path) 
    nx.draw(graph, node_color=node_color, with_labels=True)
    plt.savefig(output_path)

def display_graph(graph, node_color=None):
    # plt.figure changes the current active figure to a new one
    plt.figure(random.randint(1, 1000))
    nx.draw(graph, node_color=node_color, with_labels=True)
    plt.show()

def generate_graph(n, save=False, output_dir=DEFAULT_OUTPUT_PATH):
    graph = nx.Graph()
    color_map = []

    for i in range(0,n):
        color = random.randint(1, 3)
        color_map.append(color)
        graph.add_node(i)
        for v in range(0,graph.number_of_nodes()-1):
            if color_map[v] != color:
                x = random.randint(1,2)
                if x == 1:
                    graph.add_edge(v, i)

    # permutation test
    color_names_first = color_graph(color_map)  
    color_names_second = color_graph(color_map) 

    if save:
        output_dir_path_obj = Path(output_dir)
        if not output_dir_path_obj.exists():
            output_dir_path_obj.mkdir(parents=True)

        gen_output_path = lambda suff: f"{output_dir}/graph_{suff}.png"
        save_graph(graph, output_path=gen_output_path(n))
        save_graph(graph, color_names_first, output_path=gen_output_path(f"{n}_first_colour"))
        save_graph(graph, color_names_second, output_path=gen_output_path(f"{n}_second_colour"))
    else:
        display_graph(graph)
        display_graph(graph, color_names_first) 
        display_graph(graph, color_names_second)

    return graph, color_map

def hash(value):
    return sha256(value.encode()).hexdigest()

def commit(message):
    # hex
    key = "{0:x}".format(getrandbits(256))
    commitment = hash(key+message)
    return key, commitment 

def verify_commitment(commitment, key, message):
    return commitment == hash(key+message)


#if __name__ == "__main__":
#    message = "Wlazł kotek na płotek"
#    key, commitment = commit(message)
#    print(verify_commitment(commitment, key, message))


## hash zwraca pary wierzchołków których kolory mają być sprawdzone
g, color_map = generate_graph(35) ## powinno być ponad 128 krawędzi, po jednej dla każdego symbolu z ASCII - jednoznacznie przypisanie krawędzi znakowi


def commit_colors(colors):
    commitments = []
    keys = []
    for color in colors:
        new_key, new_commitment = commit(color)
        keys.append(new_key)
        commitments.append(new_commitment)
    return keys, commitments


## poprawka 
def hash_m_to_edge(m, g):
    ## prawdopodobieństwo przypadkowego trafienia = 1/6
    # negl = 1/(6^x), negl = 1/(2^80) ~ 1/(10^24)
    # negl ~ 1/(6^31) ~ 1/(10^24), więc prawdopodobieństwo zgadnięcia negl dla liczby krawędzi >= 31
    while len(m) < 31:
        m = m + " "
    edges = [e for e in g.edges()]
    symbols = [c for c in m]
    result = []
    if len(edges) < 128:
        print("generated graph incorrect - try again ")
        return result
    ## tworzę sumę wszystkich symboli w wiadomości mod |E|
    # dzięki temu neśli wiadomość zmieniła się tylko w jednym miejscu to wciąż wszystkie krawędzie będą inne niż 
    # dla oryginalnej wiadomości     
    suma = 0
    for i in range(0, len(symbols)):
        suma = (suma + ord(symbols[i])) % g.number_of_edges()

    for i in range(0, len(symbols)):
        s = (ord(symbols[i]) + suma) % g.number_of_edges() ## dla każdego symbolu z wiadomości przypisuje wartość dla tego znaku w ASCII + suma dla całej wiadomości
        suma = (suma + s) % g.number_of_edges()
        ## ten numer traktuje jako numer krawędzi który muszę sprawdzić 
        result.append(edges[s])
    
    return result



def sign_m(m, graph, color_map):

    edges_to_test = hash_m_to_edge(m, graph)
    signature = []
    ##  tworzę i commitmentów o i kolorowaniach
    # colors1 = color_graph(color_map) ## commitmenty mają zadeklarowane jakieś kolorowania

    # każda krawędz powinna mieć kolor z i-tego commitmentu # tu wszystkie z jednego
    commitments_array = []
    for i in edges_to_test:
        new_colors = color_graph(color_map)
        keys, commitments = commit_colors(new_colors)
        commitments_array.append((keys, commitments))
        x = (new_colors[i[0]], new_colors[i[1]])
        signature.append(x)

    return signature, commitments_array


def verify(m, graph, commitments, signature):
    edges_to_test = hash_m_to_edge(m, graph)
    iterator = 0

    if len(edges_to_test) != len(signature): ## jeśli ilość krawędzi się nie zgadza 
        return False

    for edge in edges_to_test:
    
        key1, commitment1 = commitments[iterator][0][edge[0]], commitments[iterator][1][edge[0]]
        key2, commitment2 = commitments[iterator][0][edge[1]], commitments[iterator][1][edge[1]]
        msg1 = signature[iterator][0]
        msg2 = signature[iterator][1]
        is_good1 = verify_commitment(commitment1, key1, msg1)
        is_good2 = verify_commitment(commitment2, key2, msg2)
     
        if msg1 == msg2:
            return False
        if not (is_good1 or is_good2):
            return False

        iterator += 1
    return True


text = "Kogo lisek przyodzieje"
signature, commitements = sign_m(text, g, color_map)
print(verify(text, g, commitements, signature))

print(verify("Kogo lisek przyodzieja", g, commitements, signature))
print(verify("Kogo Lisek przyodzieje", g, commitements, signature))
print(verify("inna dlugosc14", g, commitements, signature))
print(verify("Inny tekst tej dlugosc", g, commitements, signature))
