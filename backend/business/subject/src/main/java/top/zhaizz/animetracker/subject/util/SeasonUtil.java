package top.zhaizz.animetracker.subject.util;

import java.time.LocalDate;

/**
 * 季度计算工具类
 */
public class SeasonUtil {

    private SeasonUtil() {}

    /**
     * 根据年份和季度获取日期范围
     *
     * @param year   年份
     * @param quarter 季度: winter/spring/summer/autumn
     * @return [startDate, endDate]
     */
    public static LocalDate[] getSeasonRange(int year, String quarter) {
        return switch (quarter.toLowerCase()) {
            case "winter" -> new LocalDate[]{ LocalDate.of(year, 1, 1),  LocalDate.of(year, 3, 31) };
            case "spring" -> new LocalDate[]{ LocalDate.of(year, 4, 1),  LocalDate.of(year, 6, 30) };
            case "summer" -> new LocalDate[]{ LocalDate.of(year, 7, 1),  LocalDate.of(year, 9, 30) };
            case "autumn" -> new LocalDate[]{ LocalDate.of(year, 10, 1), LocalDate.of(year, 12, 31) };
            default -> throw new IllegalArgumentException("Invalid quarter: " + quarter);
        };
    }
}
