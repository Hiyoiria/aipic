/**
 * ╔══════════════════════════════════════════════════════════════╗
 * ║               实验参数配置 / Experiment Config               ║
 * ║          修改此文件即可调整实验核心参数，无需改动其他代码          ║
 * ╚══════════════════════════════════════════════════════════════╝
 */

export const EXPERIMENT_CONFIG = {
  /**
   * 干预材料页最短停留时间（秒）
   * Minimum stay duration on the intervention page (seconds)
   *
   * 被试必须等待此时间后才能点击"继续"按钮
   */
  interventionMinStaySeconds: 3,

  /**
   * 图像判断任务展示的图片总数（fixedImageIds 为 null 时生效）
   */
  totalImages: 24,

  /**
   * 固定使用的图片 ID 列表（设为 null 则退回到 totalImages 随机抽取模式）
   */
  fixedImageIds: [
    // AI (12张)
    'ai_01', 'ai_02', 'ai_04', 'ai_06', 'ai_08', 'ai_09',
    'ai_11', 'ai_13', 'ai_15', 'ai_16', 'ai_18', 'ai_19',
    // Real (12张)
    'real_01', 'real_02', 'real_03', 'real_04', 'real_05', 'real_06',
    'real_11', 'real_12', 'real_14', 'real_15', 'real_16', 'real_20',
  ] as string[] | null,
};

/**
 * ╔══════════════════════════════════════════════════════════════╗
 * ║      Google Lens 仿真面板配置 / Lens Panel Config           ║
 * ║    控制搜索结果的呈现方式：数量、布局、尺寸等                   ║
 * ╚══════════════════════════════════════════════════════════════╝
 *
 * 搜索结果数据与实验系统分离，存放在 public/data/lens-results.json
 * 此处仅控制前端呈现参数
 */
export const LENS_CONFIG = {
  /**
   * 每张图片展示的搜索结果数量
   * Number of search results displayed per image
   *
   * 如果 JSON 数据中结果多于此数，截取前 N 条
   * 如果少于此数，全部展示
   */
  resultsPerImage: 6,

  /**
   * 结果缩略图尺寸（px）
   * Thumbnail dimensions in the result list
   */
  thumbnail: {
    width: 80,
    height: 80,
  },

  /**
   * 面板宽度（桌面端，px）
   * Panel width on desktop
   */
  panelWidth: 480,

  /**
   * 面板最大高度（vh）
   * Panel max height
   */
  panelMaxHeightMobile: 85,  // vh, 移动端底部抽屉
  panelMaxHeightDesktop: 80, // vh, 桌面端居中卡片

  /**
   * 搜索源图预览尺寸（px）
   * Source image preview size in the panel header
   */
  sourcePreview: {
    width: 64,
    height: 64,
  },

  /**
   * 结果布局模式
   * Layout mode for search results
   * - 'list': 纵向列表，每行一条（左图右文）
   * - 'grid': 网格布局，每行多条
   */
  layout: 'list' as 'list' | 'grid',

  /**
   * 网格布局时每行的列数（仅 layout='grid' 时生效）
   * Number of columns in grid layout
   */
  gridColumns: 2,

  /**
   * 滚动触发日志的阈值（px）
   * Scroll distance threshold to trigger SCROLL_LENS log
   */
  scrollLogThreshold: 50,
};
