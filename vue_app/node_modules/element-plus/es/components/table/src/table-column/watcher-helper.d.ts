import type { ComputedRef } from 'vue';
import type { DefaultRow } from '../table/defaults';
import type { TableColumnCtx } from './defaults';
declare function useWatcher<T extends DefaultRow>(owner: ComputedRef<any>, props_: Partial<TableColumnCtx<T>>): {
    registerComplexWatchers: () => void;
    registerNormalWatchers: () => void;
};
export default useWatcher;
