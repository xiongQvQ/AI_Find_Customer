import type { default as CascaderNode } from './node';
import type { PropType } from 'vue';
declare function __VLS_template(): {
    empty?(_: {}): any;
};
declare const __VLS_component: import("vue").DefineComponent<{
    nodes: {
        type: PropType<CascaderNode[]>;
        required: true;
    };
    index: {
        type: NumberConstructor;
        required: true;
    };
}, {}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, Record<string, any>, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    nodes: {
        type: PropType<CascaderNode[]>;
        required: true;
    };
    index: {
        type: NumberConstructor;
        required: true;
    };
}>>, {}>;
declare const _default: __VLS_WithTemplateSlots<typeof __VLS_component, ReturnType<typeof __VLS_template>>;
export default _default;
type __VLS_WithTemplateSlots<T, S> = T & {
    new (): {
        $slots: S;
    };
};
