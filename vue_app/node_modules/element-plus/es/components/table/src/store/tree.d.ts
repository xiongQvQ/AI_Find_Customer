import type { WatcherPropsData } from '.';
import type { DefaultRow, TreeNode } from '../table/defaults';
export interface TreeData extends TreeNode {
    children?: string[];
    lazy?: boolean;
    loaded?: boolean;
}
declare function useTree<T extends DefaultRow>(watcherData: WatcherPropsData<T>): {
    loadData: (row: T, key: string, treeNode: TreeNode) => void;
    loadOrToggle: (row: T) => void;
    toggleTreeExpansion: (row: T, expanded?: boolean) => void;
    updateTreeExpandKeys: (value: string[]) => void;
    updateTreeData: (ifChangeExpandRowKeys?: boolean, ifExpandAll?: boolean) => void;
    updateKeyChildren: (key: string, data: T[]) => void;
    normalize: (data: T[]) => Record<string, TreeData>;
    states: {
        expandRowKeys: import("vue").Ref<string[]>;
        treeData: import("vue").Ref<Record<string, TreeData>>;
        indent: import("vue").Ref<number>;
        lazy: import("vue").Ref<boolean>;
        lazyTreeNodeMap: import("vue").Ref<Record<string, T[]>>;
        lazyColumnIdentifier: import("vue").Ref<string>;
        childrenColumnName: import("vue").Ref<string>;
        checkStrictly: import("vue").Ref<boolean>;
    };
};
export default useTree;
