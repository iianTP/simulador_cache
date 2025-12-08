# Importações necessárias para funcionalidades diversas
import numpy as np                      # Biblioteca para computação numérica
import random                          # Biblioteca padrão para geração de números aleatórios
from collections import deque          # Deque (fila dupla) para simulações de políticas de cache
import dearpygui.dearpygui as dpg     # Biblioteca GUI para interface gráfica
from cache_simulator_GUI import gerar_padrao_realista, is_power_of_two


class Cache:
    def __init__(self,size,algorithm,asc):
        self.size = size
        self.algorithm = algorithm
        self.asc = asc
        self.hits = 0
        self.misses = 0
        self.storage = None
        self.hit_log = []

class CacheMultinivel:
    def __init__(self):
        self.cache_list:list[Cache] = []
        self.memory_size = None
        self.accesses = None
        self.n_simulations = None
        self.prob_temp = None
        self.prob_esp = None
        self.prob_hot = None
        self.blocks = None
        self.simulate_alg = {
            'FIFO': self.simulate_FIFO,
            'LRU': self.simulate_LRU,
            'LFU': self.simulate_LFU,
            'Random': self.simulate_RANDOM
        }
        self.hot_spots = [
            64, 1024, 8192, 32768, 131072, 262144, 524288, 786432, 983040
        ]
        self.resultados = []

    def add_cache(self,cache:Cache):
        self.cache_list.append(cache)

    def update_cache(self,sender:str,app_data):
        level = int(sender[-1])
        match sender:
            case 'memory_size_multi':
                self.memory_size = app_data
                return
            case 'acessos_multi':
                self.accesses = app_data
                return
            case 'n_simulacoes_multi':
                self.n_simulations = app_data
                return
            case 'prob_temporal_multi':
                self.prob_temp = app_data
                return
            case 'prob_espacial_multi':
                self.prob_esp = app_data
                return
            case 'prob_quente_multi':
                self.prob_hot = app_data
                return
            case 'blocos_multi':
                self.blocks = [int(b.strip()) for b in app_data.split(",")]
                return

        if sender.startswith('tamanho_cache'):
            self.cache_list[level].size = app_data
            return
        if sender.startswith('associatividade'):
            self.cache_list[level].algorithm = app_data
            return
        if sender.startswith('combo_algoritmo'):
            self.cache_list[level].asc = app_data
            return

    def delete_cache(self):
        self.cache_list.pop()

    def display(self):
        for i,cache in enumerate(self.cache_list):
            print(f'- L{i} -')
            print(f'---- size: {cache.size} ')
            print(f'---- algorithm: {cache.algorithm}')
            print(f'---- asc: {cache.asc}')

        # Simulação de cache com política de substituição FIFO
    def simulate_FIFO(self,cache:Cache, padrao_acesso, cache_lines, bloco_tamanho, level=0):

        associatividade, storage, hit_log = cache.asc, cache.storage, cache.hit_log

        num_conjuntos = cache_lines // associatividade
        cache = storage if storage else [[] for _ in range(num_conjuntos)]  # Lista de conjuntos de cache
        hits, misses = 0, 0
        conjunto_log = []

        for endereco in padrao_acesso:
            bloco = endereco // bloco_tamanho
            conjunto = bloco % num_conjuntos
            conjunto_atual = cache[conjunto]

            if bloco in conjunto_atual:
                hits += 1
                hit_log.append(1)
            else:
                misses += 1
                hit_log.append(0)

                if level < len(self.cache_list):
                    next_cache = self.cache_list[level]
                    next_cache_lines = next_cache.size // bloco_tamanho
                    self.simulate_alg[next_cache.algorithm](next_cache, padrao_acesso, next_cache_lines, bloco_tamanho, level+1)

                if len(conjunto_atual) < associatividade:
                    conjunto_atual.append(bloco)
                else:
                    conjunto_atual.pop(0)  # Remove o mais antigo
                    conjunto_atual.append(bloco)

            conjunto_log.append(conjunto)

        return conjunto_log

    # ------------------------------------------------------------------------------
    # Simulação de cache com política de substituição LRU (Least Recently Used)
    def simulate_LRU(self, cache: Cache, padrao_acesso, cache_lines, bloco_tamanho, level=0):

        associatividade, storage, hit_log = cache.asc, cache.storage, cache.hit_log

        num_conjuntos = cache_lines // associatividade
        cache = storage if storage else [deque() for _ in range(num_conjuntos)]
        hits, misses = 0, 0
        conjunto_log = []

        for endereco in padrao_acesso:
            bloco = endereco // bloco_tamanho
            conjunto = bloco % num_conjuntos
            conjunto_atual = cache[conjunto]

            if bloco in conjunto_atual:
                hits += 1
                hit_log.append(1)
                conjunto_atual.remove(bloco)      # Remove e reinsere no fim (mais recente)
                conjunto_atual.append(bloco)
            else:
                misses += 1
                hit_log.append(0)

                if level < len(self.cache_list):
                    next_cache = self.cache_list[level]
                    next_cache_lines = next_cache.size // bloco_tamanho
                    self.simulate_alg[next_cache.algorithm](next_cache, padrao_acesso, next_cache_lines, bloco_tamanho, level+1)

                if len(conjunto_atual) >= associatividade:
                    conjunto_atual.popleft()      # Remove o menos recentemente usado
                conjunto_atual.append(bloco)

            conjunto_log.append(conjunto)

        return conjunto_log

    # ------------------------------------------------------------------------------
    # Simulação de cache com política de substituição LFU (Least Frequently Used)
    def simulate_LFU(self, cache:Cache,padrao_acesso, cache_lines, bloco_tamanho, level=0):

        associatividade, storage, hit_log = cache.asc, cache.storage, cache.hit_log

        num_conjuntos = cache_lines // associatividade
        cache = storage if storage else  [{} for _ in range(num_conjuntos)]  # Dict: bloco -> frequência
        hits, misses = 0, 0
        conjunto_log = []

        for endereco in padrao_acesso:
            bloco = endereco // bloco_tamanho
            conjunto = bloco % num_conjuntos
            conjunto_atual = cache[conjunto]

            if bloco in conjunto_atual:
                hits += 1
                hit_log.append(1)
                conjunto_atual[bloco] += 1
            else:
                misses += 1
                hit_log.append(0)
                
                if level < len(self.cache_list):
                    next_cache = self.cache_list[level]
                    next_cache_lines = next_cache.size // bloco_tamanho
                    self.simulate_alg[next_cache.algorithm](next_cache, padrao_acesso, next_cache_lines, bloco_tamanho, level+1)

                if len(conjunto_atual) < associatividade:
                    conjunto_atual[bloco] = 1
                else:
                    bloco_remover = min(conjunto_atual, key=conjunto_atual.get)
                    del conjunto_atual[bloco_remover]
                    conjunto_atual[bloco] = 1

            conjunto_log.append(conjunto)

        return conjunto_log

    # ------------------------------------------------------------------------------
    # Simulação de cache com política de substituição aleatória (RANDOM)
    def simulate_RANDOM(self,cache:Cache,padrao_acesso, cache_lines, bloco_tamanho, level=0):

        associatividade, storage, hit_log = cache.asc, cache.storage, cache.hit_log

        num_conjuntos = cache_lines // associatividade
        cache = storage if storage else  [[] for _ in range(num_conjuntos)]
        hits, misses = 0, 0
        conjunto_log = []

        for endereco in padrao_acesso:
            bloco = endereco // bloco_tamanho
            conjunto = bloco % num_conjuntos
            conjunto_atual = cache[conjunto]

            if bloco in conjunto_atual:
                hits += 1
                hit_log.append(1)
            else:
                misses += 1
                hit_log.append(0)
                
                if level < len(self.cache_list):
                    next_cache = self.cache_list[level]
                    next_cache_lines = next_cache.size // bloco_tamanho
                    self.simulate_alg[next_cache.algorithm](next_cache, padrao_acesso, next_cache_lines, bloco_tamanho, level+1)

                if len(conjunto_atual) < associatividade:
                    conjunto_atual.append(bloco)
                else:
                    idx_remover = random.randint(0, associatividade - 1)
                    conjunto_atual[idx_remover] = bloco

            conjunto_log.append(conjunto)

        return conjunto_log

    
    def simulate(self):

        self.resultados.clear()
        contador_barra = 0
        progresso = 0.01		# Mostra um andamento mínimo na barra de progresso para indicar que a nova simulação iniciou
        dpg.set_value("barra", progresso)
        dpg.set_value("texto", "Simulação Iniciada")
        for block in self.blocks:
            contador_barra += 1		
            progresso = contador_barra / len(self.blocks) 
            curr_cache = self.cache_list[0]
            cache_lines = curr_cache.size // block
            taxas_acerto = self.simulate_monte_carlo(
                curr_cache,
                cache_lines,
                block
            )
            dpg.set_value("barra", progresso)
            dpg.set_value("texto", f"{int(progresso*100)}% concluído")
            self.resultados.append((block, taxas_acerto))
            dpg.split_frame()  # Permite que a interface atualize

        if self.resultados:
            tamanhos, taxas = zip(*self.resultados)
            texto = f"Tamanhos_de_bloco = [{', '.join(str(int(t)) for t in tamanhos)}];\n"
            texto += f"Taxa_media_de_acerto = [{', '.join(f'{float(t):.6f}' for t in taxas)}];"
        
            # Atualiza o conteúdo da caixa de texto na interface
            dpg.set_value("resultados_box", texto)

        return
    
    def simulate_monte_carlo(self,cache:Cache,cache_lines, bloco_tamanho):
        taxas_acerto = []
        hits_totais = []
        misses_totais = []
        probs = [self.prob_temp,self.prob_esp,self.prob_hot]
        for _ in range(self.n_simulations):
            padrao = gerar_padrao_realista(self.accesses, self.memory_size, self.hot_spots, *probs, bloco_tamanho)
            
            # Seleciona e executa o algoritmo de substituição

            self.simulate_alg[cache.algorithm](padrao, cache_lines, cache.asc, bloco_tamanho, cache.storage, cache.hit_log)

            hits, misses, taxa_acerto = self.calc_hits()
            self.clear_hits()
            
            # Armazena resultados desta simulação
            taxas_acerto.append(taxa_acerto)
            hits_totais.append(hits)
            misses_totais.append(misses)

        # Exibe estatísticas gerais
        print(f"--- Resultados: {self.accesses} Acessos - Bloco de {bloco_tamanho} ---\n")
        print(f"Média da Taxa de Acerto: {np.mean(taxas_acerto):.2f}")
        print(f"Desvio Padrão da Taxa de Acerto: {np.std(taxas_acerto):.2f}")
        print(f"Máximo: {max(taxas_acerto):.2f}, Mínimo: {min(taxas_acerto):.2f}")

        # Parte do plot do mapa de acessos. COmentada porque NÃO FUNCIONA!!!!!
            # if i == 0:
                # mapa_temporal_blocos(padrao, memory_size, bloco_tamanho, resolucao_temporal=100)

        print(f"--- Resultados: {self.accesses} Acessos - Bloco de {bloco_tamanho} ---\n")
        print(f"Média da Taxa de Acerto: {np.mean(taxas_acerto):.4f}")
        print(f"Desvio padrão da Taxa de Acerto: {np.std(taxas_acerto):.4f}\n")   # print(f"Total médio de acessos: {acessos}")

        return np.mean(taxas_acerto)
    
    def calc_hits(self):
        hits = sum([sum(cache.hit_log) for cache in self.cache_list])
        misses = len(self.cache_list[0].hit_log) - hits
        taxa_acerto = hits / len(self.cache_list[0].hit_log)
        return hits, misses, taxa_acerto

    def clear_hits(self):
        for cache in self.cache_list:
            cache.hit_log = []

    def run_simulation(self):

        if not (2**20 <= self.memory_size <= 2**30) or (self.memory_size & (self.memory_size-1)) != 0:
            dpg.set_value("mensagem_erro", "Erro: Memory Size deve ser potência de 2 entre 2^20 e 2^30.")
            return
        for cache in self.cache_list:
            if not is_power_of_two(cache.asc):
                dpg.set_value("mensagem_erro", "Erro: Associatividade deve ser potência de 2 maior que zero.")
                return

            if (cache.size & (cache.size-1)) != 0 or cache.size >= self.memory_size:
                dpg.set_value("mensagem_erro", "Erro: Tamanho da Cache deve ser potência de 2 e menor que Memory Size.")
                return

            for bloco in self.blocks:
                if bloco <= 0 or bloco >= self.memory_size or not is_power_of_two(bloco):
                    dpg.set_value("mensagem_erro", f"Tamanho do Bloco deve ser potência de 2 e menor que Memory Size. Valor fornecido: {bloco}")
                    return
                cache_lines = cache.size // bloco
                num_conjuntos = cache_lines // cache.asc
                if num_conjuntos < 1:
                    dpg.set_value("mensagem_erro", f"Erro: Associatividade {cache.asc} inválida para bloco {bloco}.")
                    return

        if not (0 <= self.prob_temp <= 1) or not (0 <= self.prob_esp <= 1) or not (0 <= self.prob_hot <= 1):
            dpg.set_value("mensagem_erro", "Erro: Probabilidades devem ser entre 0 e 1.")
            return
        
        self.simulate()

