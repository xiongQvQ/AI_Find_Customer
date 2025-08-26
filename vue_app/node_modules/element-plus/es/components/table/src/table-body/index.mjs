import { defineComponent, getCurrentInstance, inject, watch, onUnmounted, h } from 'vue';
import useLayoutObserver from '../layout-observer.mjs';
import { removePopper } from '../util.mjs';
import { TABLE_INJECTION_KEY } from '../tokens.mjs';
import useRender from './render-helper.mjs';
import defaultProps from './defaults.mjs';
import { useNamespace } from '../../../../hooks/use-namespace/index.mjs';
import { addClass, removeClass } from '../../../../utils/dom/style.mjs';
import { isClient } from '@vueuse/core';
import { rAF } from '../../../../utils/raf.mjs';

var TableBody = defineComponent({
  name: "ElTableBody",
  props: defaultProps,
  setup(props) {
    var _a;
    const instance = getCurrentInstance();
    const parent = inject(TABLE_INJECTION_KEY);
    const ns = useNamespace("table");
    const { wrappedRowRender, tooltipContent, tooltipTrigger } = useRender(props);
    const { onColumnsChange, onScrollableChange } = useLayoutObserver(parent);
    const hoveredCellList = [];
    watch((_a = props.store) == null ? void 0 : _a.states.hoverRow, (newVal, oldVal) => {
      var _a2, _b;
      const el = instance == null ? void 0 : instance.vnode.el;
      const rows = Array.from((el == null ? void 0 : el.children) || []).filter((e) => e == null ? void 0 : e.classList.contains(`${ns.e("row")}`));
      let rowNum = newVal;
      const childNodes = (_a2 = rows[rowNum]) == null ? void 0 : _a2.childNodes;
      if (childNodes == null ? void 0 : childNodes.length) {
        let control = 0;
        const indexes = Array.from(childNodes).reduce((acc, item, index) => {
          var _a3, _b2;
          if (((_a3 = childNodes[index]) == null ? void 0 : _a3.colSpan) > 1) {
            control = (_b2 = childNodes[index]) == null ? void 0 : _b2.colSpan;
          }
          if (item.nodeName !== "TD" && control === 0) {
            acc.push(index);
          }
          control > 0 && control--;
          return acc;
        }, []);
        indexes.forEach((rowIndex) => {
          var _a3;
          rowNum = newVal;
          while (rowNum > 0) {
            const preChildNodes = (_a3 = rows[rowNum - 1]) == null ? void 0 : _a3.childNodes;
            if (preChildNodes[rowIndex] && preChildNodes[rowIndex].nodeName === "TD" && preChildNodes[rowIndex].rowSpan > 1) {
              addClass(preChildNodes[rowIndex], "hover-cell");
              hoveredCellList.push(preChildNodes[rowIndex]);
              break;
            }
            rowNum--;
          }
        });
      } else {
        hoveredCellList.forEach((item) => removeClass(item, "hover-cell"));
        hoveredCellList.length = 0;
      }
      if (!((_b = props.store) == null ? void 0 : _b.states.isComplex.value) || !isClient)
        return;
      rAF(() => {
        const oldRow = rows[oldVal];
        const newRow = rows[newVal];
        if (oldRow && !oldRow.classList.contains("hover-fixed-row")) {
          removeClass(oldRow, "hover-row");
        }
        if (newRow) {
          addClass(newRow, "hover-row");
        }
      });
    });
    onUnmounted(() => {
      var _a2;
      (_a2 = removePopper) == null ? void 0 : _a2();
    });
    return {
      ns,
      onColumnsChange,
      onScrollableChange,
      wrappedRowRender,
      tooltipContent,
      tooltipTrigger
    };
  },
  render() {
    const { wrappedRowRender, store } = this;
    const data = (store == null ? void 0 : store.states.data.value) || [];
    return h("tbody", { tabIndex: -1 }, [
      data.reduce((acc, row) => {
        return acc.concat(wrappedRowRender(row, acc.length));
      }, [])
    ]);
  }
});

export { TableBody as default };
//# sourceMappingURL=index.mjs.map
