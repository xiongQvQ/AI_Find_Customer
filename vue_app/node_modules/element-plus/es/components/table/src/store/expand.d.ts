import type { Ref } from 'vue';
import type { WatcherPropsData } from '.';
import type { DefaultRow } from '../table/defaults';
declare function useExpand<T extends DefaultRow>(watcherData: WatcherPropsData<T>): {
    updateExpandRows: () => void;
    toggleRowExpansion: (row: T, expanded?: boolean) => void;
    setExpandRowKeys: (rowKeys: (string | number)[]) => void;
    isRowExpanded: (row: T) => boolean;
    states: {
        expandRows: Ref<T[]>;
        defaultExpandAll: Ref<boolean>;
    };
};
export default useExpand;
