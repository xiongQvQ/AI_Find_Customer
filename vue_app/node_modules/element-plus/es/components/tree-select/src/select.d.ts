import type { Ref } from 'vue';
import type { SelectInstance } from 'element-plus/es/components/select';
import type { TreeInstance } from 'element-plus/es/components/tree';
export declare const useSelect: (props: any, { attrs, emit }: {
    attrs: any;
    emit: any;
}, { select, tree, key, }: {
    select: Ref<SelectInstance | undefined>;
    tree: Ref<TreeInstance | undefined>;
    key: Ref<string>;
}) => any;
