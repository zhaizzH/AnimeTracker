package top.zhaizz.client.util;

import java.time.LocalDate;

/**
 * 季度工具类
 */
public class SeasonUtil {
    private SeasonUtil() {}

    /** 获取指定年份季度的起止日期 */
    public static LocalDate[] getSeasonRange(int year, String quarter) {
        return switch (quarter.toLowerCase()) {
            case "winter" -> new LocalDate[]{ LocalDate.of(year, 1, 1),  LocalDate.of(year, 3, 31) };
            case "spring" -> new LocalDate[]{ LocalDate.of(year, 4, 1),  LocalDate.of(year, 6, 30) };
            case "summer" -> new LocalDate[]{ LocalDate.of(year, 7, 1),  LocalDate.of(year, 9, 30) };
            case "autumn" -> new LocalDate[]{ LocalDate.of(year, 10, 1), LocalDate.of(year, 12, 31) };
            default -> throw new IllegalArgumentException("Invalid quarter: " + quarter);
        };
    }

    /** 获取当前季度 */
    public static String getCurrentQuarter() {
        return switch (LocalDate.now().getMonth()) {
            case JANUARY, FEBRUARY, MARCH -> "winter";
            case APRIL, MAY, JUNE -> "spring";
            case JULY, AUGUST, SEPTEMBER -> "summer";
            case OCTOBER, NOVEMBER, DECEMBER -> "autumn";
        };
    }

    /** 获取当前年份 */
    public static int getCurrentYear() { return LocalDate.now().getYear(); }
}
