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
   * 图像判断任务展示的图片总数
   * Total number of images shown in the judgment task
   *
   * - 必须为偶数（AI:Real = 1:1）
   * - 如果小于图片池总数(40)，将随机抽取，保证AI和Real各一半
   * - 如果等于图片池总数，则使用全部图片
   * - 最大不超过图片池总数（目前为40: 20AI + 20Real）
   */
  totalImages: 2,
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
