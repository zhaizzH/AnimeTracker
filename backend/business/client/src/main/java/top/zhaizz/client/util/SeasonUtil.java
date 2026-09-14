package top.zhaizz.client.util;

import java.time.LocalDate;

/**
 * 季度工具类：季度字符串与年份日期范围换算，并提供当前季度/年份。
 */
public class SeasonUtil {

    /**
     * 获取指定年份季度的起止日期。
     * @param year 年份筛选值
     * @param quarter 季度名称 winter、spring、summer 或 autumn，忽略大小写，不可为空
     * @return 长度为 2 的日期数组，依次为季度首日与末日
     * @throws IllegalArgumentException 不支持的季度名称
     * @throws NullPointerException 季度名称为空
     */
    public static LocalDate[] getSeasonRange(int year, String quarter) {
        return switch (quarter.toLowerCase()) {
            case "winter" -> new LocalDate[]{LocalDate.of(year, 1, 1), LocalDate.of(year, 3, 31)};
            case "spring" -> new LocalDate[]{LocalDate.of(year, 4, 1), LocalDate.of(year, 6, 30)};
            case "summer" -> new LocalDate[]{LocalDate.of(year, 7, 1), LocalDate.of(year, 9, 30)};
            case "autumn" -> new LocalDate[]{LocalDate.of(year, 10, 1), LocalDate.of(year, 12, 31)};
            default -> throw new IllegalArgumentException("Invalid quarter: " + quarter);
        };
    }

    /**
     * 获取当前季度。
     * @return 系统默认时区当前日期所属的英文季度名称
     */
    public static String getCurrentQuarter() {
        return switch (LocalDate.now().getMonth()) {
            case JANUARY, FEBRUARY, MARCH -> "winter";
            case APRIL, MAY, JUNE -> "spring";
            case JULY, AUGUST, SEPTEMBER -> "summer";
            case OCTOBER, NOVEMBER, DECEMBER -> "autumn";
        };
    }

    /**
     * 获取当前年份。
     * @return 系统默认时区当前日期的年份
     */
    public static int getCurrentYear() {
        return LocalDate.now().getYear();
    }
}
