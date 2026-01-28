<template>
  <div class="chart-container">
    <h2>Top 10 Maiores Despesas (R$)</h2>
    <Bar v-if="loaded" :data="chartData" :options="chartOptions" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Bar } from 'vue-chartjs';
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js';
import api from '../api';

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale);

const loaded = ref(false);
const chartData = ref(null);
const chartOptions = { responsive: true };

onMounted(async () => {
  const res = await api.get('/estatisticas');
  const data = res.data; // Já vem ordenado do backend

  chartData.value = {
    labels: data.map(d => d.razao_social.substring(0, 20) + '...'), // Corta nome longo
    datasets: [{
      label: 'Despesa Total',
      backgroundColor: '#f87979',
      data: data.map(d => d.valor_total)
    }]
  };
  loaded.value = true;
});
</script>

<style scoped>
.chart-container { max-width: 800px; margin: 0 auto; }
</style>