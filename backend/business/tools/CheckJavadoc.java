import com.sun.source.doctree.*;
import com.sun.source.tree.*;
import com.sun.source.util.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import javax.tools.*;

/**
 * 使用 JDK 语法树检查全部源码声明及 Javadoc 标签，不运行注解处理器
 */
public class CheckJavadoc {
    /** 当前扫描到的违规总数 */
    private static int errors;
    /** 已检查的源码声明数 */
    private static int declarations;

    /**
     * 扫描指定源码根目录，发现违规时退出非零
     * @param args 唯一参数为源码根目录
     * @throws Exception 文件读取或编译器初始化失败
     */
    public static void main(String[] args) throws Exception {
        Path root = Path.of(args.length == 0 ? "backend/business" : args[0]);
        List<Path> files;
        try (var paths = Files.walk(root)) {
            files = paths.filter(p -> p.toString().endsWith(".java"))
                    .filter(p -> !p.toString().replace('\\', '/').contains("/target/"))
                    .sorted().toList();
        }
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
        try (var manager = compiler.getStandardFileManager(diagnostics, null, StandardCharsets.UTF_8)) {
            JavacTask task = (JavacTask) compiler.getTask(null, manager, diagnostics,
                    List.of("-proc:none", "-encoding", "UTF-8", "--release", "21"), null,
                    manager.getJavaFileObjectsFromPaths(files));
            DocTrees docs = DocTrees.instance(task);
            for (CompilationUnitTree unit : task.parse()) {
                new TreePathScanner<Void, Void>() {
                    /** {@inheritDoc}
                     * <p>检查有名称的类型，不要求匿名类产生虚构类型注释
                     */
                    @Override public Void visitClass(ClassTree node, Void unused) {
                        if (!node.getSimpleName().toString().isEmpty()) check(node);
                        return super.visitClass(node, unused);
                    }
                    /** {@inheritDoc}
                     * <p>检查手写方法和构造器，参数不作为字段处理
                     */
                    @Override public Void visitMethod(MethodTree node, Void unused) {
                        check(node);
                        return super.visitMethod(node, unused);
                    }
                    /** {@inheritDoc}
                     * <p>仅检查成员字段；局部变量和参数无需声明 Javadoc
                     */
                    @Override public Void visitVariable(VariableTree node, Void unused) {
                        if (getCurrentPath().getParentPath().getLeaf() instanceof ClassTree owner) {
                            // javac 将 record 组件表示为字段，契约由 record 的 @param 承载
                            if (owner.getKind() != Tree.Kind.RECORD ||
                                    node.getModifiers().getFlags().contains(javax.lang.model.element.Modifier.STATIC)) {
                                check(node);
                            }
                        }
                        return super.visitVariable(node, unused);
                    }
                    /**
                     * 核对单个声明的文档、参数顺序和返回值标签
                     * @param node 当前声明
                     */
                    private void check(Tree node) {
                        declarations++;
                        DocCommentTree doc = docs.getDocCommentTree(getCurrentPath());
                        long pos = docs.getSourcePositions().getStartPosition(unit, node);
                        String location = Path.of(unit.getSourceFile().toUri()) + ":" + unit.getLineMap().getLineNumber(pos);
                        if (doc == null) { fail(location, "missing Javadoc"); return; }
                        String text = docs.getDocComment(getCurrentPath());
                        if (text.contains("验证对应组件在该场景下保持既定契约") ||
                                text.contains("执行更新业务流程") || text.contains("数据对象中的")) {
                            fail(location, "mechanical summary");
                        }
                        new DocTreeScanner<Void, Void>() {
                            /** {@inheritDoc}
                     * <p>拒绝 JDK 文档解析器识别的格式错误
                     */
                            @Override public Void visitErroneous(com.sun.source.doctree.ErroneousTree bad, Void p) {
                                fail(location, "invalid Javadoc: " + bad.getDiagnostic().getMessage(Locale.ROOT));
                                return null;
                            }
                        }.scan(doc, null);
                        boolean inherited = text.contains("{@inheritDoc}");
                        if (inherited) {
                            if (!(node instanceof MethodTree m) || m.getReturnType() == null ||
                                    m.getModifiers().getAnnotations().stream().noneMatch(a -> a.getAnnotationType().toString().equals("Override"))) {
                                fail(location, "inheritDoc requires an overriding method");
                            }
                            return; // 继承来源与链接由完整 classpath 下的 doclint 校验
                        }
                        if (doc.getFullBody().stream().filter(t -> t instanceof TextTree).map(t -> ((TextTree)t).getBody()).collect(java.util.stream.Collectors.joining()).codePoints().noneMatch(c -> Character.UnicodeScript.of(c) == Character.UnicodeScript.HAN)) {
                            fail(location, "summary must explain behavior in Chinese");
                        }
                        List<String> expected = new ArrayList<>();
                        if (node instanceof MethodTree m) {
                            m.getTypeParameters().forEach(p -> expected.add("<" + p.getName() + ">"));
                            m.getParameters().forEach(p -> expected.add(p.getName().toString()));
                        } else if (node instanceof ClassTree c) {
                            c.getTypeParameters().forEach(p -> expected.add("<" + p.getName() + ">"));
                            if (c.getKind() == Tree.Kind.RECORD) c.getMembers().stream()
                                    .filter(t -> t instanceof VariableTree)
                                    .map(t -> (VariableTree)t)
                                    .filter(v -> !v.getModifiers().getFlags().contains(javax.lang.model.element.Modifier.STATIC))
                                    .forEach(v -> expected.add(v.getName().toString()));
                        }
                        List<String> actual = new ArrayList<>();
                        int returns = 0;
                        for (DocTree tag : doc.getBlockTags()) {
                            if (tag instanceof ParamTree p) {
                                actual.add(p.isTypeParameter() ? "<" + p.getName() + ">" : p.getName().toString());
                                if (p.getDescription().isEmpty()) fail(location, "empty @param " + p.getName());
                            }
                            if (tag instanceof com.sun.source.doctree.ReturnTree r) {
                                returns++;
                                if (r.getDescription().isEmpty()) fail(location, "empty @return");
                            }
                        }
                        if (!expected.equals(actual)) fail(location, "@param expected=" + expected + " actual=" + actual);
                        boolean needsReturn = node instanceof MethodTree m && m.getReturnType() != null &&
                                !m.getReturnType().toString().equals("void");
                        if ((needsReturn && returns != 1) || (!needsReturn && returns != 0)) {
                            fail(location, "@return count=" + returns);
                        }
                    }
                }.scan(unit, null);
            }
        }
        for (var d : diagnostics.getDiagnostics()) if (d.getKind() == Diagnostic.Kind.ERROR) {
            fail(String.valueOf(d.getSource()) + ":" + d.getLineNumber(), d.getMessage(Locale.ROOT));
        }
        System.out.println("Checked " + files.size() + " files, " + declarations + " declarations, " + errors + " violations");
        if (errors > 0) System.exit(1);
    }
    /**
     * 输出可定位的违规证据
     * @param location 文件及行号
     * @param message 违规原因
     */
    private static void fail(String location, String message) {
        errors++;
        System.out.println(location + " " + message);
    }
}
