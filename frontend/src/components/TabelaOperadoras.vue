<template>
  <div class="container">
    <h1>Consulta de Operadoras ANS</h1>
    
    <div class="controls">
      <input 
        v-model="search" 
        @input="buscarOperadoras" 
        placeholder="Buscar por Razão Social ou CNPJ..." 
        class="search-input"
      />
    </div>

    <table class="data-table">
      <thead>
        <tr>
          <th>Registro ANS</th>
          <th>CNPJ</th>
          <th>Razão Social</th>
          <th>UF</th>
          <th>Modalidade</th>
          <th>Ações</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="op in operadoras" :key="op.registro_ans">
          <td>{{ op.registro_ans }}</td>
          <td>{{ op.cnpj }}</td>
          <td>{{ op.razao_social }}</td>
          <td>{{ op.uf }}</td>
          <td>{{ op.modalidade }}</td>
          <td>
            <button @click="verDetalhes(op.registro_ans)">Ver Despesas</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="pagination">
      <button :disabled="page === 1" @click="mudarPagina(-1)">Anterior</button>
      <span>Página {{ page }} de {{ totalPaginas }}</span>
      <button :disabled="page >= totalPaginas" @click="mudarPagina(1)">Próxima</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../api';
import { useRouter } from 'vue-router';

const router = useRouter();
const operadoras = ref([]);
const search = ref('');
const page = ref(1);
const total = ref(0);
const limit = 10;
const totalPaginas = ref(1);

const carregarDados = async () => {
  try {
    const res = await api.get('/operadoras', {
      params: { page: page.value, limit: limit, search: search.value }
    });
    operadoras.value = res.data.data;
    total.value = res.data.total;
    totalPaginas.value = Math.ceil(total.value / limit);
  } catch (error) {
    console.error("Erro ao carregar:", error);
  }
};

const buscarOperadoras = () => {
  page.value = 1; // Reseta para pág 1 na busca
  carregarDados();
};

const mudarPagina = (delta) => {
  page.value += delta;
  carregarDados();
};

const verDetalhes = (reg) => {
  router.push(`/operadora/${reg}`);
};

onMounted(() => {
  carregarDados();
});
</script>

<style scoped>
.container { padding: 20px; font-family: sans-serif; }
.search-input { padding: 8px; width: 300px; margin-bottom: 20px; }
.data-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
.data-table th, .data-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
.data-table th { background-color: #f2f2f2; }
.pagination { display: flex; gap: 10px; align-items: center; }
button { padding: 5px 10px; cursor: pointer; }
</style>