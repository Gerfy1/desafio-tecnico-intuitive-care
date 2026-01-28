<template>
  <div class="container" v-if="operadora">
    <button @click="$router.push('/')" class="btn-voltar">← Voltar</button>
    
    <div class="header">
      <h1>{{ operadora.razao_social }}</h1>
      <p><strong>CNPJ:</strong> {{ operadora.cnpj }}</p>
      <p><strong>Registro ANS:</strong> {{ operadora.registro_ans }}</p>
      <p><strong>Modalidade:</strong> {{ operadora.modalidade }} - {{ operadora.uf }}</p>
    </div>

    <h2>Histórico de Despesas</h2>
    
    <div v-if="loading" class="loading">Carregando despesas...</div>
    
    <table v-else class="data-table">
      <thead>
        <tr>
          <th>Ano</th>
          <th>Trimestre</th>
          <th>Conta</th>
          <th>Valor (R$)</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in despesas" :key="index">
          <td>{{ item.ano }}</td>
          <td>{{ item.trimestre }}</td>
          <td>{{ item.conta }}</td>
          <td class="valor">{{ formatarMoeda(item.valor) }}</td>
        </tr>
        <tr v-if="despesas.length === 0">
          <td colspan="4">Nenhuma despesa registrada para os filtros aplicados.</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import api from '../api';

const route = useRoute();
const operadora = ref(null);
const despesas = ref([]);
const loading = ref(true);

const formatarMoeda = (valor) => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
};

onMounted(async () => {
  const id = route.params.id; // Pega o ID da URL
  try {
    // 1. Busca dados cadastrais
    const resOp = await api.get(`/operadoras/${id}`);
    operadora.value = resOp.data;

    // 2. Busca despesas
    const resDesp = await api.get(`/operadoras/${id}/despesas`);
    despesas.value = resDesp.data;
  } catch (error) {
    console.error("Erro ao carregar detalhes:", error);
    alert("Erro ao carregar dados. Verifique o console.");
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.container { padding: 20px; font-family: sans-serif; }
.header { background: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #ddd; }
.btn-voltar { background: #666; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; margin-bottom: 15px; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
.data-table th { background-color: #eee; }
.valor { text-align: right; font-family: monospace; }
</style>