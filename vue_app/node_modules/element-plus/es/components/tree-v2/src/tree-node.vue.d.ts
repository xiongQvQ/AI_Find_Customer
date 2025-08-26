import type { CheckboxValueType } from 'element-plus/es/components/checkbox';
import type { TreeNode } from './types';
declare const _default: import("vue").DefineComponent<{
    readonly node: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => TreeNode) | (() => TreeNode) | ((new (...args: any[]) => TreeNode) | (() => TreeNode))[], unknown, unknown, () => import("element-plus/es/utils").Mutable<{
        readonly key: -1;
        readonly level: -1;
        readonly data: {};
    }>, boolean>;
    readonly expanded: BooleanConstructor;
    readonly checked: BooleanConstructor;
    readonly indeterminate: BooleanConstructor;
    readonly showCheckbox: BooleanConstructor;
    readonly disabled: BooleanConstructor;
    readonly current: BooleanConstructor;
    readonly hiddenExpandIcon: BooleanConstructor;
    readonly itemSize: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, number, boolean>;
}, {}, unknown, {}, {}, import("vue").ComponentOptionsMixin, import("vue").ComponentOptionsMixin, {
    click: (node: TreeNode, e: MouseEvent) => void;
    drop: (node: TreeNode, e: DragEvent) => void;
    toggle: (node: TreeNode) => void;
    check: (node: TreeNode, checked: CheckboxValueType) => void;
}, string, import("vue").VNodeProps & import("vue").AllowedComponentProps & import("vue").ComponentCustomProps, Readonly<import("vue").ExtractPropTypes<{
    readonly node: import("element-plus/es/utils").EpPropFinalized<(new (...args: any[]) => TreeNode) | (() => TreeNode) | ((new (...args: any[]) => TreeNode) | (() => TreeNode))[], unknown, unknown, () => import("element-plus/es/utils").Mutable<{
        readonly key: -1;
        readonly level: -1;
        readonly data: {};
    }>, boolean>;
    readonly expanded: BooleanConstructor;
    readonly checked: BooleanConstructor;
    readonly indeterminate: BooleanConstructor;
    readonly showCheckbox: BooleanConstructor;
    readonly disabled: BooleanConstructor;
    readonly current: BooleanConstructor;
    readonly hiddenExpandIcon: BooleanConstructor;
    readonly itemSize: import("element-plus/es/utils").EpPropFinalized<NumberConstructor, unknown, unknown, number, boolean>;
}>> & {
    onDrop?: ((node: TreeNode, e: DragEvent) => any) | undefined;
    onClick?: ((node: TreeNode, e: MouseEvent) => any) | undefined;
    onToggle?: ((node: TreeNode) => any) | undefined;
    onCheck?: ((node: TreeNode, checked: CheckboxValueType) => any) | undefined;
}, {
    readonly disabled: boolean;
    readonly expanded: boolean;
    readonly current: boolean;
    readonly indeterminate: boolean;
    readonly checked: boolean;
    readonly node: TreeNode;
    readonly itemSize: number;
    readonly showCheckbox: boolean;
    readonly hiddenExpandIcon: boolean;
}>;
export default _default;
