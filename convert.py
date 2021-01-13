import os
import pickle
import warnings
import subprocess

import numpy as np
from numpy.lib.stride_tricks import as_strided
from scipy.io import wavfile
from scipy.sparse import lil_matrix
from scipy.signal import get_window
from scipy.signal import resample as scipy_resample

def extract_data(song_file, song_directory="./mp3-songs", data_directory="./songs-data"):
    rate, data = wavfile.read(os.path.join(song_directory, song_file))
    monodata = np.mean(data, axis=1).astype('float64')

    ratio = 22050.0 / rate
    n_samples = int(np.ceil(monodata.shape[0] * ratio))
    resampled = scipy_resample(monodata, n_samples)

    cqtdata = np.abs(cqt(resampled, 22050))
    spectrogram = np.transpose(cqtdata)**2

    info = {'spectrogram': spectrogram, 'sample_rate': 22050}
    with open(os.path.join(data_directory, song_file[:-4]), 'wb') as datafile:
        pickle.dump(info, datafile)

def convert_songs_to_data(directory_base=".", mp3_folder="mp3-songs",
        song_folder="songs", data_folder="songs-data",
        playlist_folder="playlists", playlist_name = "playlist", append_pl=False):
    mp3_directory = os.path.join(directory_base, mp3_folder)
    song_directory = os.path.join(directory_base, song_folder)
    data_directory = os.path.join(directory_base, data_folder)
    playlist_directory = os.path.join(directory_base, playlist_folder)

    # get all mp3 files (and possibly a txt)
    files = os.listdir(mp3_directory)
    playlist = ""

    print("Extracting music data")
    track_count = len(files)
    track_count_on = 1
    for file in files:
        if file[-4:] == ".mp3":
            if os.path.exists(os.path.join(song_directory, file)) and os.path.exists(os.path.join(data_directory, file[:-4])):
                print("({}/{}) Song exists: {}".format(track_count_on, track_count, file))
                os.remove(os.path.join(mp3_directory, file))
            else:
                wav_name = file[:-4]+".wav"
                subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-i', file, wav_name], cwd=mp3_directory)
                extract_data(wav_name, mp3_directory, data_directory)
                os.rename(os.path.join(mp3_directory, file), os.path.join(song_directory, file))
                os.remove(os.path.join(mp3_directory, wav_name))
                print("({}/{}) Data extracted: {}".format(track_count_on, track_count, file))
            playlist += file[:-4] + "\n"
        else:
            print("({}/{}) Erranous file removed: {}".format(track_count_on, track_count, file))
        track_count_on += 1

    if append_pl:
        playlist_name = playlist_name + ".txt"
        with open(os.path.join(playlist_directory, playlist_name), "a") as file:
            file.write(playlist)
    else:
        i = -1
        while os.path.exists(os.path.join(playlist_directory, playlist_name + ".txt")):
            i += 1
            playlist_name = playlist_name + "_{}".format(i)
        playlist_name = playlist_name + ".txt"

        with open(os.path.join(playlist_directory, playlist_name), "w") as file:
            file.write(playlist)

    with open(os.path.join(playlist_directory, "all.txt"), "a") as file:
        file.write(playlist)

if __name__ == '__main__':
    convert_songs_to_data(mp3_folder="mp3-songs0")


# cqt code taken from librosa (would just import but pip import does not always work)
def cqt(y, sr=22050):
    hop_length = 512
    fmin = 32.703
    n_bins = 96
    gamma = 0
    bins_per_octave = 12
    tuning = 0.0
    filter_scale = 1
    norm = 1
    sparsity = 0.01
    window = "hann"
    scale = True
    pad_mode = "reflect"
    res_type = "kaiser_fast"
    dtype = np.complex128

    # How many octaves are we dealing with?
    n_octaves = int(8)
    n_filters = 8

    len_orig = len(y)

    # Relative difference in frequency between any two consecutive bands
    alpha = 2.0 ** (1.0 / bins_per_octave) - 1

    # First thing, get the freqs of the top octave
    freqs = fmin * (2.0 ** (np.arange(0, n_bins, dtype=float) / bins_per_octave))
    freqs = freqs[-bins_per_octave:]

    fmin_t = np.min(freqs)
    fmax_t = np.max(freqs)

    # Determine required resampling quality
    Q = float(filter_scale) / alpha
    filter_cutoff = (fmax_t * (1 + 0.5 * 1.50018310546875 / Q))
    nyquist = sr / 2.0

    vqt_resp = []

    # Now do the recursive bit
    my_y, my_sr, my_hop = y, sr, hop_length

    # Iterate down the octaves
    for i in range(n_octaves):
        # Resample (except first time)
        if i > 0:
            if len(my_y) < 2:
                raise ValueError(
                    "Input signal length={} is too short for "
                    "{:d}-octave CQT/VQT".format(len_orig, n_octaves)
                )

            my_y = audio_resample(my_y, 2, 1, res_type=res_type, scale=True)

            my_sr /= 2.0
            my_hop //= 2

        fft_basis, n_fft, _ = __cqt_filter_fft(
            my_sr,
            fmin_t * 2.0 ** -i,
            n_filters,
            bins_per_octave,
            filter_scale,
            norm,
            sparsity,
            window=window,
            gamma=gamma,
            dtype=dtype,
        )
        # Re-scale the filters to compensate for downsampling
        fft_basis[:] *= np.sqrt(2 ** i)

        # Compute the vqt filter response and append to the stack
        vqt_resp.append(
            # __cqt_response(my_y, n_fft, my_hop, fft_basis, pad_mode, dtype=dtype)
            fft_basis.dot(lib_stft(my_y, n_fft=n_fft, hop_length=my_hop, window="ones", pad_mode=pad_mode, dtype=dtype))
        )

    V = __trim_stack(vqt_resp, n_bins, dtype)

    if scale:
        lengths = filters_constant_q_lengths(
            sr,
            fmin,
            n_bins=n_bins,
            bins_per_octave=bins_per_octave,
            window=window,
            filter_scale=filter_scale,
            gamma=gamma,
        )
        V /= np.sqrt(lengths[:, np.newaxis])

    return V


# helper functions for resampling taken from resampy (similar download problem to librosa)

def resample(x, sr_orig, sr_new, axis=-1, filter='kaiser_best', directory="."):
    
    if sr_orig <= 0:
        raise ValueError('Invalid sample rate: sr_orig={}'.format(sr_orig))

    if sr_new <= 0:
        raise ValueError('Invalid sample rate: sr_new={}'.format(sr_new))

    sample_ratio = float(sr_new) / sr_orig

    # Set up the output shape
    shape = list(x.shape)
    shape[axis] = int(shape[axis] * sample_ratio)

    if shape[axis] < 1:
        raise ValueError('Input signal length={} is too small to '
                         'resample from {}->{}'.format(x.shape[axis], sr_orig, sr_new))

    # Preserve contiguity of input (if it exists)
    # If not, revert to C-contiguity by default
    if x.flags['F_CONTIGUOUS']:
        order = 'F'
    else:
        order = 'C'

    y = np.zeros(shape, dtype=x.dtype, order=order)

    # interp_win, precision, _ = pickle.load(os.path.join(directory, "filterValue.bin"))
    interp_win, precision = None, None
    with open(os.path.join(directory, "filterValue.bin"), 'rb') as datafile:
        interp_win, precision, _ = pickle.load(datafile)

    if sample_ratio < 1:
        interp_win *= sample_ratio

    interp_delta = np.zeros_like(interp_win)
    interp_delta[:-1] = np.diff(interp_win)

    # Construct 2d views of the data with the resampling axis on the first dimension
    x_2d = x.swapaxes(0, axis).reshape((x.shape[axis], -1))
    y_2d = y.swapaxes(0, axis).reshape((y.shape[axis], -1))
    resample_f(x_2d, y_2d, sample_ratio, interp_win, interp_delta, precision)

    return y

def resample_f(x, y, sample_ratio, interp_win, interp_delta, num_table):

    scale = min(1.0, sample_ratio)
    time_increment = 1.0/sample_ratio
    index_step = int(scale * num_table)
    time_register = 0.0

    n = 0
    frac = 0.0
    index_frac = 0.0
    offset = 0
    eta = 0.0
    weight = 0.0

    nwin = interp_win.shape[0]
    n_orig = x.shape[0]
    n_out = y.shape[0]
    n_channels = y.shape[1]

    for t in range(n_out):
        # Grab the top bits as an index to the input buffer
        n = int(time_register)

        # Grab the fractional component of the time index
        frac = scale * (time_register - n)

        # Offset into the filter
        index_frac = frac * num_table
        offset = int(index_frac)

        # Interpolation factor
        eta = index_frac - offset

        # Compute the left wing of the filter response
        i_max = min(n + 1, (nwin - offset) // index_step)
        for i in range(i_max):

            weight = (interp_win[offset + i * index_step] + eta * interp_delta[offset + i * index_step])
            for j in range(n_channels):
                y[t, j] += weight * x[n - i, j]

        # Invert P
        frac = scale - frac

        # Offset into the filter
        index_frac = frac * num_table
        offset = int(index_frac)

        # Interpolation factor
        eta = index_frac - offset

        # Compute the right wing of the filter response
        k_max = min(n_orig - n - 1, (nwin - offset)//index_step)
        for k in range(k_max):
            weight = (interp_win[offset + k * index_step] + eta * interp_delta[offset + k * index_step])
            for j in range(n_channels):
                y[t, j] += weight * x[n + k + 1, j]

        # Increment the time register
        time_register += time_increment

# from librosa (audio.resample)
def audio_resample(
    y, orig_sr, target_sr, res_type="kaiser_best", fix=True, scale=False, **kwargs
):

    if orig_sr == target_sr:
        return y

    ratio = float(target_sr) / orig_sr

    n_samples = int(np.ceil(y.shape[-1] * ratio))

    # y_hat = resample(y, orig_sr, target_sr, filter=res_type, axis=-1)
    y_hat = scipy_resample(y, n_samples)

    if fix:
        y_hat = fix_length(y_hat, n_samples, **kwargs)

    if scale:
        y_hat /= np.sqrt(ratio)

    return np.asfortranarray(y_hat, dtype=y.dtype)

def fix_length(data, size, axis=-1, **kwargs):
    kwargs.setdefault("mode", "constant")

    n = data.shape[axis]

    if n > size:
        slices = [slice(None)] * data.ndim
        slices[axis] = slice(0, size)
        return data[tuple(slices)]

    elif n < size:
        lengths = [(0, 0)] * data.ndim
        lengths[axis] = (0, size - n)
        return np.pad(data, lengths, **kwargs)

    return data

# from librosa (in constantq.py)
def __cqt_filter_fft(
    sr,
    fmin,
    n_bins,
    bins_per_octave,
    filter_scale,
    norm,
    sparsity,
    hop_length=None,
    window="hann",
    gamma=0.0,
    dtype=np.complex,
):
    """Generate the frequency domain constant-Q filter basis."""

    basis, lengths = filters_constant_q(
        sr,
        fmin=fmin,
        n_bins=n_bins,
        bins_per_octave=bins_per_octave,
        filter_scale=filter_scale,
        norm=norm,
        pad_fft=True,
        window=window,
        gamma=gamma,
    )

    # Filters are padded up to the nearest integral power of 2
    n_fft = basis.shape[1]

    if hop_length is not None and n_fft < 2.0 ** (1 + np.ceil(np.log2(hop_length))):

        n_fft = int(2.0 ** (1 + np.ceil(np.log2(hop_length))))

    # re-normalize bases with respect to the FFT window length
    basis *= lengths[:, np.newaxis] / float(n_fft)

    # FFT and retain only the non-negative frequencies
    fft_basis = np.fft.fft(basis, n=n_fft, axis=1)[:, : (n_fft // 2) + 1]

    # sparsify the basis
    fft_basis = sparsify_rows(fft_basis, quantile=sparsity, dtype=dtype)

    return fft_basis, n_fft, lengths

# from librosa (in utils.py)
def sparsify_rows(x, quantile=0.01, dtype=None):

    if x.ndim == 1:
        x = x.reshape((1, -1))

    if dtype is None:
        dtype = x.dtype

    x_sparse = lil_matrix(x.shape, dtype=dtype)

    mags = np.abs(x)
    norms = np.sum(mags, axis=1, keepdims=True)

    mag_sort = np.sort(mags, axis=1)
    cumulative_mag = np.cumsum(mag_sort / norms, axis=1)

    threshold_idx = np.argmin(cumulative_mag < quantile, axis=1)

    for i, j in enumerate(threshold_idx):
        idx = np.where(mags[i] >= mag_sort[i, j])
        x_sparse[i, idx] = x[i, idx]

    return x_sparse.tocsr()

# from librosa (constant_q in filters.py)
def filters_constant_q(
    sr,
    fmin=None,
    n_bins=84,
    bins_per_octave=12,
    window="hann",
    filter_scale=1,
    pad_fft=True,
    norm=1,
    dtype=np.complex64,
    gamma=0,
    **kwargs,
):

    if fmin is None:
        fmin = note_to_hz("C1")

    # Pass-through parameters to get the filter lengths
    lengths = filters_constant_q_lengths(
        sr,
        fmin,
        n_bins=n_bins,
        bins_per_octave=bins_per_octave,
        window=window,
        filter_scale=filter_scale,
        gamma=gamma,
    )

    freqs = fmin * (2.0 ** (np.arange(n_bins, dtype=float) / bins_per_octave))

    # Build the filters
    filters = []
    for ilen, freq in zip(lengths, freqs):
        # Build the filter: note, length will be ceil(ilen)
        sig = np.exp(
            np.arange(-ilen // 2, ilen // 2, dtype=float) * 1j * 2 * np.pi * freq / sr
        )

        # Apply the windowing function
        sig = sig * __float_window(window)(len(sig))

        # Normalize
        sig = util_normalize(sig, norm=norm)

        filters.append(sig)

    # Pad and stack
    max_len = max(lengths)
    if pad_fft:
        max_len = int(2.0 ** (np.ceil(np.log2(max_len))))
    else:
        max_len = int(np.ceil(max_len))

    filters = np.asarray(
        [pad_center(filt, max_len, **kwargs) for filt in filters], dtype=dtype
    )

    return filters, np.asarray(lengths)

# from librosa (constant_q_lengths in filters.py)
def filters_constant_q_lengths(
    sr, fmin, n_bins=84, bins_per_octave=12, window="hann", filter_scale=1, gamma=0
):

    # Q should be capitalized here, so we suppress the name warning
    # pylint: disable=invalid-name
    alpha = 2.0 ** (1.0 / bins_per_octave) - 1.0
    Q = float(filter_scale) / alpha

    # Compute the frequencies
    freq = fmin * (2.0 ** (np.arange(n_bins, dtype=float) / bins_per_octave))

    if freq[-1] * (1 + 0.5 * (1.50018310546875) / Q) > sr / 2.0:
        raise ValueError("Filter pass-band lies beyond Nyquist")

    # Convert frequencies to filter lengths
    lengths = Q * sr / (freq + gamma / alpha)

    return lengths

# from librosa (in filters.py)
def __float_window(window_spec):
    """Decorator function for windows with fractional input.
    This function guarantees that for fractional ``x``, the following hold:
    1. ``__float_window(window_function)(x)`` has length ``np.ceil(x)``
    2. all values from ``np.floor(x)`` are set to 0.
    For integer-valued ``x``, there should be no change in behavior.
    """

    def _wrap(n, *args, **kwargs):
        """The wrapped window"""
        n_min, n_max = int(np.floor(n)), int(np.ceil(n))

        window = get_window_a(window_spec, n_min)

        if len(window) < n_max:
            window = np.pad(window, [(0, n_max - len(window))], mode="constant")

        window[n_min:] = 0.0

        return window

    return _wrap

# from librosa (get_window in filters.py)
def get_window_a(window, Nx, fftbins=True):
    if callable(window):
        return window(Nx)

    elif isinstance(window, (str, tuple)) or np.isscalar(window):
        # TODO: if we add custom window functions in librosa, call them here

        return get_window(window, Nx, fftbins=fftbins)

    elif isinstance(window, (np.ndarray, list)):
        if len(window) == Nx:
            return np.asarray(window)

        raise ValueError(
            "Window size mismatch: " "{:d} != {:d}".format(len(window), Nx)
        )
    else:
        raise ValueError("Invalid window specification: {}".format(window))

# from librosa (normalize in utils.py)
def util_normalize(S, norm=np.inf, axis=0, threshold=None, fill=None):
    # Avoid div-by-zero
    if threshold is None:

        S2 = np.asarray(S)

        # Only floating types generate a tiny
        if np.issubdtype(S2.dtype, np.floating) or np.issubdtype(
            S2.dtype, np.complexfloating
        ):
            dtype = S2.dtype
        else:
            dtype = np.float32

        threshold = np.finfo(dtype).tiny

    elif threshold <= 0:
        raise ValueError(
            "threshold={} must be strictly " "positive".format(threshold)
        )

    if fill not in [None, False, True]:
        raise ValueError("fill={} must be None or boolean".format(fill))

    if not np.all(np.isfinite(S)):
        raise ValueError("Input must be finite")

    # All norms only depend on magnitude, let's do that first
    mag = np.abs(S).astype(np.float)

    # For max/min norms, filling with 1 works
    fill_norm = 1

    if norm == np.inf:
        length = np.max(mag, axis=axis, keepdims=True)

    elif norm == -np.inf:
        length = np.min(mag, axis=axis, keepdims=True)

    elif norm == 0:
        if fill is True:
            raise ValueError("Cannot normalize with norm=0 and fill=True")

        length = np.sum(mag > 0, axis=axis, keepdims=True, dtype=mag.dtype)

    elif np.issubdtype(type(norm), np.number) and norm > 0:
        length = np.sum(mag ** norm, axis=axis, keepdims=True) ** (1.0 / norm)

        if axis is None:
            fill_norm = mag.size ** (-1.0 / norm)
        else:
            fill_norm = mag.shape[axis] ** (-1.0 / norm)

    elif norm is None:
        return S

    else:
        raise ValueError("Unsupported norm: {}".format(repr(norm)))

    # indices where norm is below the threshold
    small_idx = length < threshold

    Snorm = np.empty_like(S)
    if fill is None:
        # Leave small indices un-normalized
        length[small_idx] = 1.0
        Snorm[:] = S / length

    elif fill:
        # If we have a non-zero fill value, we locate those entries by
        # doing a nan-divide.
        # If S was finite, then length is finite (except for small positions)
        length[small_idx] = np.nan
        Snorm[:] = S / length
        Snorm[np.isnan(Snorm)] = fill_norm
    else:
        # Set small values to zero by doing an inf-divide.
        # This is safe (by IEEE-754) as long as S is finite.
        length[small_idx] = np.inf
        Snorm[:] = S / length

    return Snorm

# from librosa (in utils.py)
def pad_center(data, size, axis=-1, **kwargs):
    kwargs.setdefault("mode", "constant")

    n = data.shape[axis]

    lpad = int((size - n) // 2)

    lengths = [(0, 0)] * data.ndim
    lengths[axis] = (lpad, int(size - n - lpad))

    if lpad < 0:
        raise ValueError(
            ("Target size ({:d}) must be " "at least input size ({:d})").format(size, n)
        )

    return np.pad(data, lengths, **kwargs)

# from librosa (stft in spectrum.py)
def lib_stft(
    y,
    n_fft=2048,
    hop_length=None,
    win_length=None,
    window="hann",
    center=True,
    dtype=None,
    pad_mode="reflect",
):

    # By default, use the entire frame
    if win_length is None:
        win_length = n_fft

    # Set the default hop, if it's not already specified
    if hop_length is None:
        hop_length = int(win_length // 4)

    fft_window = get_window_a(window, win_length, fftbins=True)

    # Pad the window out to n_fft size
    fft_window = pad_center(fft_window, n_fft)

    # Reshape so that the window can be broadcast
    fft_window = fft_window.reshape((-1, 1))

    # Pad the time series so that frames are centered
    if center:
        if n_fft > y.shape[-1]:
            warnings.warn(
                "n_fft={} is too small for input signal of length={}".format(
                    n_fft, y.shape[-1]
                )
            )

        y = np.pad(y, int(n_fft // 2), mode=pad_mode)

    elif n_fft > y.shape[-1]:
        raise ValueError(
            "n_fft={} is too small for input signal of length={}".format(
                n_fft, y.shape[-1]
            )
        )

    # Window the time series.
    y_frames = util_frame(y, frame_length=n_fft, hop_length=hop_length)

    # Pre-allocate the STFT matrix
    stft_matrix = np.empty(
        (int(1 + n_fft // 2), y_frames.shape[1]), dtype=dtype, order="F"
    )

    # how many columns can we fit within MAX_MEM_BLOCK?
    n_columns = 262144 // (stft_matrix.shape[0] * stft_matrix.itemsize)
    n_columns = max(n_columns, 1)

    for bl_s in range(0, stft_matrix.shape[1], n_columns):
        bl_t = min(bl_s + n_columns, stft_matrix.shape[1])

        stft_matrix[:, bl_s:bl_t] = np.fft.rfft(
            fft_window * y_frames[:, bl_s:bl_t], axis=0
        )
    return stft_matrix

# from librosa (frame in utils.py)
def util_frame(x, frame_length, hop_length, axis=-1):

    if not isinstance(x, np.ndarray):
        raise ValueError(
            "Input must be of type numpy.ndarray, " "given type(x)={}".format(type(x))
        )

    if x.shape[axis] < frame_length:
        raise ValueError(
            "Input is too short (n={:d})"
            " for frame_length={:d}".format(x.shape[axis], frame_length)
        )

    if hop_length < 1:
        raise ValueError("Invalid hop_length: {:d}".format(hop_length))

    if axis == -1 and not x.flags["F_CONTIGUOUS"]:
        warnings.warn(
            "librosa.util.frame called with axis={} "
            "on a non-contiguous input. This will result in a copy.".format(axis)
        )
        x = np.asfortranarray(x)
    elif axis == 0 and not x.flags["C_CONTIGUOUS"]:
        warnings.warn(
            "librosa.util.frame called with axis={} "
            "on a non-contiguous input. This will result in a copy.".format(axis)
        )
        x = np.ascontiguousarray(x)

    n_frames = 1 + (x.shape[axis] - frame_length) // hop_length
    strides = np.asarray(x.strides)

    new_stride = np.prod(strides[strides > 0] // x.itemsize) * x.itemsize

    if axis == -1:
        shape = list(x.shape)[:-1] + [frame_length, n_frames]
        strides = list(strides) + [hop_length * new_stride]

    elif axis == 0:
        shape = [n_frames, frame_length] + list(x.shape)[1:]
        strides = [hop_length * new_stride] + list(strides)

    else:
        raise ValueError("Frame axis={} must be either 0 or -1".format(axis))

    return as_strided(x, shape=shape, strides=strides)

# from librosa (in constantq.py)
def __trim_stack(cqt_resp, n_bins, dtype):
    """Helper function to trim and stack a collection of CQT responses"""

    max_col = min(c_i.shape[-1] for c_i in cqt_resp)
    cqt_out = np.empty((n_bins, max_col), dtype=dtype, order="F")

    # Copy per-octave data into output array
    end = n_bins
    for c_i in cqt_resp:
        # By default, take the whole octave
        n_oct = c_i.shape[0]
        # If the whole octave is more than we can fit,
        # take the highest bins from c_i
        if end < n_oct:
            cqt_out[:end] = c_i[-end:, :max_col]
        else:
            cqt_out[end - n_oct : end] = c_i[:, :max_col]

        end -= n_oct

    return cqt_out