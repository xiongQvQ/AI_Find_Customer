import type { Ref } from 'vue';
import type { DefaultRow } from '../table/defaults';
import type { WatcherPropsData } from '.';
declare function useCurrent<T extends DefaultRow>(watcherData: WatcherPropsData<T>): {
    setCurrentRowKey: (key: string) => void;
    restoreCurrentRowKey: () => void;
    setCurrentRowByKey: (key: string) => void;
    updateCurrentRow: (_currentRow: T) => void;
    updateCurrentRowData: () => void;
    states: {
        _currentRowKey: Ref<string | null>;
        currentRow: Ref<T | null>;
    };
};
export default useCurrent;
