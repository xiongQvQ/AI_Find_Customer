import type { Ref } from 'vue';
import type { SelectInstance } from 'element-plus/es/components/select';
import type { TreeInstance } from 'element-plus/es/components/tree';
export declare const useTree: (props: any, { attrs, slots, emit }: {
    attrs: any;
    slots: any;
    emit: any;
}, { select, tree, key, }: {
    select: Ref<SelectInstance | undefined>;
    tree: Ref<TreeInstance | undefined>;
    key: Ref<string>;
}) => any;
