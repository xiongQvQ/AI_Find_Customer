import { ref, computed } from 'vue';
import { useElementSize } from '@vueuse/core';

function useContainer(layout) {
  const containerEl = ref();
  const { width, height } = useElementSize(containerEl);
  const containerSize = computed(() => {
    return layout.value === "horizontal" ? width.value : height.value;
  });
  return { containerEl, containerSize };
}

export { useContainer };
//# sourceMappingURL=useContainer.mjs.map
