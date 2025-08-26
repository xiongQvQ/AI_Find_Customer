import { defineComponent, getCurrentInstance, inject, ref, computed, openBlock, createBlock, unref, normalizeClass, withCtx, createElementBlock, Fragment, renderList, createVNode, createTextVNode, toDisplayString, renderSlot, createCommentVNode } from 'vue';
import { ElScrollbar } from '../../scrollbar/index.mjs';
import { Loading } from '@element-plus/icons-vue';
import { ElIcon } from '../../icon/index.mjs';
import ElCascaderNode from './node2.mjs';
import { CASCADER_PANEL_INJECTION_KEY } from './types.mjs';
import _export_sfc from '../../../_virtual/plugin-vue_export-helper.mjs';
import { useNamespace } from '../../../hooks/use-namespace/index.mjs';
import { useLocale } from '../../../hooks/use-locale/index.mjs';
import { useId } from '../../../hooks/use-id/index.mjs';

const __default__ = defineComponent({
  name: "ElCascaderMenu"
});
const _sfc_main = /* @__PURE__ */ defineComponent({
  ...__default__,
  props: {
    nodes: {
      type: Array,
      required: true
    },
    index: {
      type: Number,
      required: true
    }
  },
  setup(__props) {
    const props = __props;
    const instance = getCurrentInstance();
    const ns = useNamespace("cascader-menu");
    const { t } = useLocale();
    const id = useId();
    let activeNode;
    let hoverTimer;
    const panel = inject(CASCADER_PANEL_INJECTION_KEY);
    const hoverZone = ref();
    const isEmpty = computed(() => !props.nodes.length);
    const isLoading = computed(() => !panel.initialLoaded);
    const menuId = computed(() => `${id.value}-${props.index}`);
    const handleExpand = (e) => {
      activeNode = e.target;
    };
    const handleMouseMove = (e) => {
      if (!panel.isHoverMenu || !activeNode || !hoverZone.value)
        return;
      if (activeNode.contains(e.target)) {
        clearHoverTimer();
        const el = instance.vnode.el;
        const { left } = el.getBoundingClientRect();
        const { offsetWidth, offsetHeight } = el;
        const startX = e.clientX - left;
        const top = activeNode.offsetTop;
        const bottom = top + activeNode.offsetHeight;
        hoverZone.value.innerHTML = `
          <path style="pointer-events: auto;" fill="transparent" d="M${startX} ${top} L${offsetWidth} 0 V${top} Z" />
          <path style="pointer-events: auto;" fill="transparent" d="M${startX} ${bottom} L${offsetWidth} ${offsetHeight} V${bottom} Z" />
        `;
      } else if (!hoverTimer) {
        hoverTimer = window.setTimeout(clearHoverZone, panel.config.hoverThreshold);
      }
    };
    const clearHoverTimer = () => {
      if (!hoverTimer)
        return;
      clearTimeout(hoverTimer);
      hoverTimer = void 0;
    };
    const clearHoverZone = () => {
      if (!hoverZone.value)
        return;
      hoverZone.value.innerHTML = "";
      clearHoverTimer();
    };
    return (_ctx, _cache) => {
      return openBlock(), createBlock(unref(ElScrollbar), {
        key: unref(menuId),
        tag: "ul",
        role: "menu",
        class: normalizeClass(unref(ns).b()),
        "wrap-class": unref(ns).e("wrap"),
        "view-class": [unref(ns).e("list"), unref(ns).is("empty", unref(isEmpty))],
        onMousemove: handleMouseMove,
        onMouseleave: clearHoverZone
      }, {
        default: withCtx(() => {
          var _a;
          return [
            (openBlock(true), createElementBlock(Fragment, null, renderList(__props.nodes, (node) => {
              return openBlock(), createBlock(ElCascaderNode, {
                key: node.uid,
                node,
                "menu-id": unref(menuId),
                onExpand: handleExpand
              }, null, 8, ["node", "menu-id"]);
            }), 128)),
            unref(isLoading) ? (openBlock(), createElementBlock("div", {
              key: 0,
              class: normalizeClass(unref(ns).e("empty-text"))
            }, [
              createVNode(unref(ElIcon), {
                size: "14",
                class: normalizeClass(unref(ns).is("loading"))
              }, {
                default: withCtx(() => [
                  createVNode(unref(Loading))
                ]),
                _: 1
              }, 8, ["class"]),
              createTextVNode(" " + toDisplayString(unref(t)("el.cascader.loading")), 1)
            ], 2)) : unref(isEmpty) ? (openBlock(), createElementBlock("div", {
              key: 1,
              class: normalizeClass(unref(ns).e("empty-text"))
            }, [
              renderSlot(_ctx.$slots, "empty", {}, () => [
                createTextVNode(toDisplayString(unref(t)("el.cascader.noData")), 1)
              ])
            ], 2)) : ((_a = unref(panel)) == null ? void 0 : _a.isHoverMenu) ? (openBlock(), createElementBlock(Fragment, { key: 2 }, [
              createCommentVNode(" eslint-disable-next-line vue/html-self-closing "),
              (openBlock(), createElementBlock("svg", {
                ref_key: "hoverZone",
                ref: hoverZone,
                class: normalizeClass(unref(ns).e("hover-zone"))
              }, null, 2))
            ], 2112)) : createCommentVNode("v-if", true)
          ];
        }),
        _: 3
      }, 8, ["class", "wrap-class", "view-class"]);
    };
  }
});
var ElCascaderMenu = /* @__PURE__ */ _export_sfc(_sfc_main, [["__file", "menu.vue"]]);

export { ElCascaderMenu as default };
//# sourceMappingURL=menu.mjs.map
