import type { default as CascaderNode } from './node';
import type { PropType } from 'vue';
declare const _default: import("vue").DefineComponent<{
    node: {
        type: PropType<CascaderNode>;
        required: true;
    };
    menuId: StringConstructor;
}, {}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    expand: (...args: any[]) => void;
}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    node: {
        type: PropType<CascaderNode>;
        required: true;
    };
    menuId: StringConstructor;
}>> & {
    onExpand?: ((...args: any[]) => any) | undefined;
}, {}>;
export default _default;
