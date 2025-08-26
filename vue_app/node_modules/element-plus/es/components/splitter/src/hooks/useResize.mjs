import { ref, computed, watch } from 'vue';
import { isPct, getPct, isPx, getPx } from './useSize.mjs';
import { NOOP } from '@vue/shared';

function useResize(panels, containerSize, pxSizes, lazy) {
  const ptg2px = (ptg) => ptg * containerSize.value || 0;
  function getLimitSize(str, defaultLimit) {
    if (isPct(str)) {
      return ptg2px(getPct(str));
    } else if (isPx(str)) {
      return getPx(str);
    }
    return str != null ? str : defaultLimit;
  }
  const lazyOffset = ref(0);
  const movingIndex = ref(null);
  let cachePxSizes = [];
  let updatePanelSizes = NOOP;
  const limitSizes = computed(() => panels.value.map((item) => [item.min, item.max]));
  watch(lazy, () => {
    if (lazyOffset.value) {
      const mouseup = new MouseEvent("mouseup", { bubbles: true });
      window.dispatchEvent(mouseup);
    }
  });
  const onMoveStart = (index) => {
    lazyOffset.value = 0;
    movingIndex.value = { index, confirmed: false };
    cachePxSizes = pxSizes.value;
  };
  const onMoving = (index, offset) => {
    var _a, _b;
    let confirmedIndex = null;
    if ((!movingIndex.value || !movingIndex.value.confirmed) && offset !== 0) {
      if (offset > 0) {
        confirmedIndex = index;
        movingIndex.value = { index, confirmed: true };
      } else {
        for (let i = index; i >= 0; i -= 1) {
          if (cachePxSizes[i] > 0) {
            confirmedIndex = i;
            movingIndex.value = { index: i, confirmed: true };
            break;
          }
        }
      }
    }
    const mergedIndex = (_b = confirmedIndex != null ? confirmedIndex : (_a = movingIndex.value) == null ? void 0 : _a.index) != null ? _b : index;
    const numSizes = [...cachePxSizes];
    const nextIndex = mergedIndex + 1;
    const startMinSize = getLimitSize(limitSizes.value[mergedIndex][0], 0);
    const endMinSize = getLimitSize(limitSizes.value[nextIndex][0], 0);
    const startMaxSize = getLimitSize(limitSizes.value[mergedIndex][1], containerSize.value || 0);
    const endMaxSize = getLimitSize(limitSizes.value[nextIndex][1], containerSize.value || 0);
    let mergedOffset = offset;
    if (numSizes[mergedIndex] + mergedOffset < startMinSize) {
      mergedOffset = startMinSize - numSizes[mergedIndex];
    }
    if (numSizes[nextIndex] - mergedOffset < endMinSize) {
      mergedOffset = numSizes[nextIndex] - endMinSize;
    }
    if (numSizes[mergedIndex] + mergedOffset > startMaxSize) {
      mergedOffset = startMaxSize - numSizes[mergedIndex];
    }
    if (numSizes[nextIndex] - mergedOffset > endMaxSize) {
      mergedOffset = numSizes[nextIndex] - endMaxSize;
    }
    numSizes[mergedIndex] += mergedOffset;
    numSizes[nextIndex] -= mergedOffset;
    lazyOffset.value = mergedOffset;
    updatePanelSizes = () => {
      panels.value.forEach((panel, index2) => {
        panel.size = numSizes[index2];
      });
      updatePanelSizes = NOOP;
    };
    if (!lazy.value) {
      updatePanelSizes();
    }
  };
  const onMoveEnd = () => {
    if (lazy.value) {
      updatePanelSizes();
    }
    lazyOffset.value = 0;
    movingIndex.value = null;
    cachePxSizes = [];
  };
  const cacheCollapsedSize = [];
  const onCollapse = (index, type) => {
    if (!cacheCollapsedSize.length) {
      cacheCollapsedSize.push(...pxSizes.value);
    }
    const currentSizes = pxSizes.value;
    const currentIndex = type === "start" ? index : index + 1;
    const targetIndex = type === "start" ? index + 1 : index;
    const currentSize = currentSizes[currentIndex];
    const targetSize = currentSizes[targetIndex];
    if (currentSize !== 0 && targetSize !== 0) {
      currentSizes[currentIndex] = 0;
      currentSizes[targetIndex] += currentSize;
      cacheCollapsedSize[index] = currentSize;
    } else {
      const totalSize = currentSize + targetSize;
      const targetCacheCollapsedSize = cacheCollapsedSize[index];
      const currentCacheCollapsedSize = totalSize - targetCacheCollapsedSize;
      currentSizes[targetIndex] = targetCacheCollapsedSize;
      currentSizes[currentIndex] = currentCacheCollapsedSize;
    }
    panels.value.forEach((panel, index2) => {
      panel.size = currentSizes[index2];
    });
  };
  return {
    lazyOffset,
    onMoveStart,
    onMoving,
    onMoveEnd,
    movingIndex,
    onCollapse
  };
}

export { useResize };
//# sourceMappingURL=useResize.mjs.map
