import type { LoadingInstance } from './loading';
import type { LoadingOptions } from './types';
import type { AppContext } from 'vue';
declare const Loading: {
    (options?: LoadingOptions): LoadingInstance;
    _context: AppContext | null;
};
export default Loading;
