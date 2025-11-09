import { ref, onMounted, onUnmounted, watch, type Ref } from 'vue';
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  BarController,
  BarElement,
  LinearScale,
  CategoryScale,
  TimeScale,
  Title,
  Tooltip,
  Legend,
  Filler,
  type ChartConfiguration,
} from 'chart.js';
import { CandlestickController, CandlestickElement } from 'chartjs-chart-financial';
import 'chartjs-adapter-date-fns';

// Register Chart.js components
Chart.register(
  LineController,
  LineElement,
  PointElement,
  BarController,
  BarElement,
  LinearScale,
  CategoryScale,
  TimeScale,
  Title,
  Tooltip,
  Legend,
  Filler,
  CandlestickController,
  CandlestickElement
);

export function useChart(canvasRef: Ref<HTMLCanvasElement | null>) {
  let chartInstance: Chart | null = null;

  const createChart = (config: ChartConfiguration) => {
    if (!canvasRef.value) return;

    // Destroy existing chart
    if (chartInstance) {
      chartInstance.destroy();
    }

    // Create new chart
    chartInstance = new Chart(canvasRef.value, config);
  };

  const updateChart = (config: ChartConfiguration) => {
    createChart(config);
  };

  const destroyChart = () => {
    if (chartInstance) {
      chartInstance.destroy();
      chartInstance = null;
    }
  };

  onUnmounted(() => {
    destroyChart();
  });

  return {
    createChart,
    updateChart,
    destroyChart,
  };
}
