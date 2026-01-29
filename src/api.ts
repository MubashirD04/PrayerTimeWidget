import { invoke } from "@tauri-apps/api/core";

export interface PrayerTimes {
    Fajr: string;
    Dhuhr: string;
    Asr: string;
    Maghrib: string;
    Isha: string;
}

export interface LocationData {
    lat: number;
    lon: number;
    city: string;
}

export const api = {
    getLocationAuto: async (): Promise<LocationData> => {
        return await invoke("get_location_auto");
    },

    searchCity: async (query: string): Promise<LocationData> => {
        return await invoke("search_city", { query });
    },

    getPrayerTimes: async (lat: number, lon: number): Promise<PrayerTimes> => {
        return await invoke("get_prayer_times_cmd", { lat, lon });
    },

    getNextPrayer: async (timings: PrayerTimes): Promise<[string, string, string]> => {
        // Returns [Name, Time, Countdown]
        return await invoke("get_next_prayer_cmd", { timings });
    },

    closeWindow: async (): Promise<void> => {
        return await invoke("close_window");
    }
};
